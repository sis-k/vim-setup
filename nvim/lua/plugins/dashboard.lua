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
    if line ~= "" then
        table.insert(lines, line)
    end
    return table.concat(lines, "\n")
end

local URL = "https://zenquotes.io/api/today"
local cache_file = vim.fn.stdpath("cache") .. "/quote_of_day.json"
local user = os.getenv("USER") or os.getenv("LOGNAME") or "there"

-- Return today's cached quote, if there is one.
local function cached_quote()
    local f = io.open(cache_file, "r")
    if not f then
        return nil
    end
    local content = f:read("*a")
    f:close()
    local ok, data = pcall(vim.json.decode, content)
    if ok and data and data.date == os.date("%Y-%m-%d") then
        return data.header
    end
end

-- Kept in vim.g because this file can be evaluated twice on a cold start.
vim.g.quote_of_day = cached_quote()

-- Fetch today's quote in the background, so a slow network can't delay startup.
-- -s: silent, -f: fail on HTTP error, --max-time: timeout.
local function fetch_quote()
    vim.system({ "curl", "-sf", "--max-time", "5", URL }, { text = true }, function(result)
        vim.schedule(function()
            local ok, json = pcall(vim.json.decode, result.stdout or "")
            if result.code ~= 0 or not ok or not json or not json[1] then
                return
            end
            local header = wrap(json[1].q or "", 60) .. "\n\n— " .. (json[1].a or "")
            vim.g.quote_of_day = header
            local f = io.open(cache_file, "w")
            if f then
                f:write(vim.json.encode({ date = os.date("%Y-%m-%d"), header = header }))
                f:close()
            end
            Snacks.dashboard.update()
        end)
    end)
end

-- Only look for a new quote when the dashboard is actually showing.
if not vim.g.quote_of_day then
    vim.api.nvim_create_autocmd("User", {
        group = vim.api.nvim_create_augroup("quote_of_day", { clear = true }),
        pattern = "SnacksDashboardOpened",
        once = true,
        callback = fetch_quote,
    })
end

return {
    "folke/snacks.nvim",
    opts = {
        dashboard = {
            sections = {
                -- A function, because the quote can arrive after the dashboard has opened.
                function()
                    return { header = vim.g.quote_of_day or ("Welcome " .. user .. "!"), padding = 2 }
                end,
                { section = "keys", gap = 1, padding = 1 },
                { section = "startup" },
            },
        },
    },
}
