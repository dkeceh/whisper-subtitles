-- srt2textplus.lua — satu Text+ per cue subtitle, template = klip terpilih di Media Pool.
-- Pakai: (1) drag .srt ke subtitle track, (2) pilih template di Media Pool,
-- (3) jalankan script ini. Hasil: track video baru berisi Text+ per cue, timing persis cue.
--   1 klip terpilih  = mode basic
--   2 klip terpilih  = mode karaoke: urut nama -> nama pertama = baris aktif,
--                      nama kedua = preview baris berikutnya (lebih rendah, di bawah)
-- Log: Workspace > Console / ResolveDebug.txt (print/error).

local buf = {}
local function log(s) buf[#buf+1] = tostring(s) end

local function wait(sec)
  if os and os.clock then
    local t0 = os.clock()
    while os.clock() - t0 < sec do end
  end
end

-- port dari Python _connected_tool: input INPS_ID -> tool yang tersambung
local function connected_tool(tool, input_id, expect_regid)
  local oki, inputs = pcall(function() return tool:GetInputList() end)
  if not oki or not inputs then return nil end
  for _, inp in pairs(inputs) do
    local oka, attrs = pcall(function() return inp:GetAttrs() end)
    if oka and attrs and attrs["INPS_ID"] == input_id then
      local oko, out = pcall(function() return inp:GetConnectedOutput() end)
      local mod = nil
      if oko and out then
        local okt, t = pcall(function() return out:GetTool() end)
        if okt then mod = t end
      end
      if mod == nil then return nil end
      if expect_regid then
        local okr, rattrs = pcall(function() return mod:GetAttrs() end)
        if not okr or not rattrs or rattrs["TOOLS_RegID"] ~= expect_regid then
          return nil
        end
      end
      return mod
    end
  end
  return nil
end

-- teks harus ditulis di tool paling dalam chain: Text+ <- Follower <- CLS
local function set_caption_text(tool, text)
  local follower = connected_tool(tool, "StyledText", "StyledTextFollower")
  if follower then
    local cls = connected_tool(follower, "Text", "StyledTextCLS")
    local target = cls or follower
    local ok = pcall(function() target:SetInput("Text", text) end)
    return ok
  end
  local ok = pcall(function() tool:SetInput("StyledText", text) end)
  return ok
end

local function first_textplus(item)
  for attempt = 1, 6 do
    local okc, comp = pcall(function() return item:GetFusionCompByIndex(1) end)
    if okc and comp then
      local okg, tools = pcall(function() return comp:GetToolList(false, "TextPlus") end)
      if okg and tools and tools[1] then return tools[1] end
    end
    if attempt < 6 then wait(0.4) end
  end
  return nil
end

local function clean_text(name)
  -- GetName mengganti line-break subtitle dengan "???"
  local t = tostring(name or ""):gsub("???", " "):gsub("^%s+", ""):gsub("%s+$", "")
  return t
end

local function main()
  local proj = resolve:GetProjectManager():GetCurrentProject()
  if not proj then error("tidak ada project aktif") end
  local tl = proj:GetCurrentTimeline()
  if not tl then error("tidak ada timeline aktif") end
  local pool = proj:GetMediaPool()

  local fps = tonumber(tl:GetSetting("timelineFrameRate"))
  if not fps then error("tidak bisa baca timeline frame rate") end
  log("fps = " .. fps .. "  timeline = " .. tl:GetName())

  -- 1. cue dari subtitle track
  local nsub = tl:GetTrackCount("subtitle") or 0
  if nsub < 1 then error("tidak ada subtitle track - drag .srt ke timeline dulu") end
  local cues = {}
  for tr = 1, nsub do
    local items = tl:GetItemListInTrack("subtitle", tr) or {}
    for _, it in ipairs(items) do
      local text = clean_text(it:GetName())
      local gs, ge = it:GetStart(), it:GetEnd()
      if text ~= "" and gs and ge and ge > gs then
        cues[#cues + 1] = { start = gs, ["end"] = ge, text = text }
      end
    end
  end
  table.sort(cues, function(a, b) return a.start < b.start end)
  log("cue dari subtitle track = " .. #cues)
  if #cues == 0 then error("subtitle track kosong - drag .srt dulu") end

  -- 2. template dari klip terpilih di Media Pool (1 = basic, 2 = karaoke)
  local sel = pool:GetSelectedClips() or {}
  if #sel < 1 or #sel > 2 then
    error("pilih 1 klip template (basic) atau 2 (karaoke) di Media Pool (terpilih: " .. #sel .. ")")
  end
  for _, mpi in ipairs(sel) do
    local okty, ctype = pcall(function() return mpi:GetClipProperty("Type") end)
    if okty and ctype == "Subtitle" then
      error("ada klip terpilih bertipe Subtitle - pilih klip template Text+ (Fusion Clip)")
    end
  end
  table.sort(sel, function(a, b)
    return tostring(a:GetName()) < tostring(b:GetName())
  end)
  local template = sel[1]
  local ptemplate = sel[2]  -- nil di mode basic
  local tname = tostring(template:GetName())
  local native_fps = tonumber(template:GetClipProperty("FPS")) or fps
  local ratio = native_fps / fps
  log("template = " .. tname .. "  native_fps = " .. native_fps ..
    (ptemplate and ("  preview = " .. tostring(ptemplate:GetName())) or "  (basic)"))

  -- 3. track video: preview dulu (lebih bawah), baru aktif (lebih atas - render di depan)
  local karaoke = ptemplate ~= nil and #cues > 1
  local ptrack = nil
  if karaoke then
    if not tl:AddTrack("video") then error("gagal AddTrack video (preview)") end
    ptrack = tl:GetTrackCount("video")
  end
  if not tl:AddTrack("video") then error("gagal AddTrack video") end
  local track = tl:GetTrackCount("video")

  local function info(c, track_index, media)
    return {
      mediaPoolItem = media or template,
      startFrame = 0,
      endFrame = math.max(1, math.floor((c["end"] - c.start) * ratio + 0.5)),
      trackIndex = track_index,
      recordFrame = c.start,
      mediaType = 1,
    }
  end

  local infos = {}
  for _, c in ipairs(cues) do
    infos[#infos + 1] = info(c, track)
  end
  local previews = {}  -- teks next-line per klip preview
  if karaoke then
    for i = 1, #cues - 1 do
      infos[#infos + 1] = info(cues[i], ptrack, ptemplate)
      previews[#previews + 1] = cues[i + 1].text
    end
  end

  local oka, items = pcall(function() return pool:AppendToTimeline(infos) end)
  if not oka or not items or #items ~= #infos then
    error("AppendToTimeline: expected " .. #infos .. " clips, got " ..
      tostring(items and #items or 0))
  end
  log("append ok: " .. #items .. " clip (aktif V" .. track ..
    (karaoke and (", preview V" .. ptrack) or "") .. ")")

  -- 4. isi teks: #cues pertama = baris aktif, sisanya = preview next-line
  local filled, failed = 0, 0
  for i, item in ipairs(items) do
    local text = i <= #cues and cues[i].text or previews[i - #cues]
    local tool = first_textplus(item)
    if tool and set_caption_text(tool, text) then
      filled = filled + 1
    else
      failed = failed + 1
      log("clip " .. i .. ": gagal set teks")
    end
  end
  log("teks terisi = " .. filled .. "/" .. #items)
  if failed > 0 then
    error("sebagian clip gagal terisi (check template) - " .. filled .. "/" .. #items ..
      "\n" .. table.concat(buf, "\n"))
  end
end

local ok, err = pcall(main)
if not ok then log("GAGAL: " .. tostring(err)) end
error("=== srt2textplus ===\n" .. table.concat(buf, "\n") .. "\n")
