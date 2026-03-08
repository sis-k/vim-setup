-- Word-wrap text at the given column width.
local function wrap(text, width)
    local lines = {}
    local line = ""
    for word in text:gmatch("%S+") do
        if #line + #word + 1 > width then
            table.insert(lines, line)
            line = word
        else
            line = line == "" and word or (line .. " " .. word)
        end
    end
    if line ~= "" then table.insert(lines, line) end
    return table.concat(lines, "\n")
end

-- Fetch today's quote from zenquotes.io, caching to disk so subsequent
-- startups are instant. Falls back to a static greeting on any failure.
local function quote_of_day()
    local cache_file = vim.fn.stdpath("cache") .. "/quote_of_day.json"
    local today = os.date("%Y-%m-%d")

    -- Return cached header if it is from today.
    local f = io.open(cache_file, "r")
    if f then
        local content = f:read("*a")
        f:close()
        local ok, data = pcall(vim.json.decode, content)
        if ok and data and data.date == today and data.header then
            return data.header
        end
    end

    -- Fetch from zenquotes. -s: silent, -f: fail on HTTP error, --max-time: timeout.
    local raw = vim.fn.system("curl -sf --max-time 5 https://zenquotes.io/api/today")
    local user = os.getenv("USER") or os.getenv("LOGNAME") or "there"

    if vim.v.shell_error ~= 0 or raw == "" then
        return "Welcome " .. user .. "!"
    end

    local ok, json = pcall(vim.json.decode, raw)
    if not ok or not json or not json[1] then
        return "Welcome " .. user .. "!"
    end

    local header = wrap(json[1].q or "", 60) .. "\n\n— " .. (json[1].a or "")

    -- Persist to cache.
    local wf = io.open(cache_file, "w")
    if wf then
        wf:write(vim.json.encode({ date = today, header = header }))
        wf:close()
    end

    return header
end

return {
    "folke/snacks.nvim",
    opts = {
        dashboard = {
            preset = {
                header = quote_of_day(),
            },
        },
    },
}
