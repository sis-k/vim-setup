-- C and C++ with CMake, cross-compilers and gdbserver.

-- clangd only runs compilers it is told to trust when it looks for system headers.
-- Trust cross-compilers in the PATH directories, rather than a glob that matches a compiler anywhere in a repo.
local function query_driver()
    local globs = {}
    for dir in vim.gsplit(vim.env.PATH or "", ":", { plain = true }) do
        if dir:sub(1, 1) == "/" then
            for _, name in ipairs({ "*-gcc", "*-g++", "*-cc", "*-c++" }) do
                table.insert(globs, dir .. "/" .. name)
            end
        end
    end
    return "--query-driver=" .. table.concat(globs, ",")
end

-- cmake-tools keeps the configure and build presets apart, so picking a configure preset would
-- leave builds running the old build preset. Pick its build preset too, or ask when there's a choice.
local function select_configure_preset()
    local cmake = require("cmake-tools")
    cmake.select_configure_preset(function(result)
        if not result:is_ok() then
            return
        end
        local config = cmake.get_config()
        local presets = require("cmake-tools.presets"):parse(config.cwd)
        local matches = vim.tbl_filter(function(name)
            return presets:get_build_preset(name).configurePreset == config.configure_preset
        end, presets:get_build_preset_names({ include_disabled = false }))
        if #matches == 1 then
            config.build_preset = matches[1]
            config:update_build_target()
            cmake.generate({})
        else
            cmake.select_build_preset()
        end
    end)
end

-- cmake-tools won't replace a compile_commands.json link that points at another build folder, so clangd would
-- keep the first preset's flags. It asks for the link's folder before linking, which is the moment to remove it.
local function compile_commands_dir()
    local cwd = vim.uv.cwd()
    local link = cwd .. "/compile_commands.json"
    local stat = vim.uv.fs_lstat(link)
    if stat and stat.type == "link" then
        vim.uv.fs_unlink(link)
    end
    return cwd
end

-- Answers are kept for the session, so reconnecting only takes a few presses of enter.
local last = { program = nil, target = "localhost:2345", gdb = nil }

local function ask(key, prompt, default, completion)
    local answer = vim.fn.input({ prompt = prompt, default = last[key] or default, completion = completion })
    last[key] = answer ~= "" and answer or last[key]
    return answer ~= "" and answer or nil
end

-- A callable config, because nvim-dap evaluates functions in separate fields in no fixed order.
local function connect_to_gdbserver(config)
    local dap = require("dap")
    local program = ask("program", "Program with symbols: ", vim.fn.getcwd() .. "/", "file")
    local target = program and ask("target", "gdbserver address: ", "")
    local multiarch = vim.fn.executable("gdb-multiarch") == 1
    local gdb = target and ask("gdb", "gdb: ", multiarch and "gdb-multiarch" or "gdb", "shellcmd")
    -- nvim-dap looks for ABORT in a field, not as the returned config.
    if not gdb then
        return vim.tbl_extend("force", config, { program = dap.ABORT })
    end
    if vim.fn.executable(gdb) == 0 then
        vim.notify(gdb .. " is not on PATH", vim.log.levels.ERROR)
        return vim.tbl_extend("force", config, { program = dap.ABORT })
    end
    return vim.tbl_extend("force", config, { program = vim.fn.fnamemodify(program, ":p"), target = target, gdb = gdb })
end

return {
    {
        "neovim/nvim-lspconfig",
        opts = function(_, opts)
            table.insert(opts.servers.clangd.cmd, query_driver())
        end,
    },
    {
        "Civitasv/cmake-tools.nvim",
        opts = {
            cmake_executor = { name = "overseer" },
            cmake_compile_commands_options = { action = "soft_link", target = compile_commands_dir },
        },
        keys = {
            { "<leader>mg", "<cmd>CMakeGenerate<cr>", desc = "Configure" },
            { "<leader>mG", ":CMakeGenerate ", desc = "Configure with Options" },
            { "<leader>mb", "<cmd>CMakeBuild<cr>", desc = "Build" },
            { "<leader>mc", "<cmd>CMakeClean<cr>", desc = "Clean" },
            { "<leader>mx", "<cmd>CMakeStopExecutor<cr>", desc = "Stop" },
            { "<leader>mp", select_configure_preset, desc = "Select Configure Preset" },
            { "<leader>mP", "<cmd>CMakeSelectBuildPreset<cr>", desc = "Select Build Preset" },
            { "<leader>mk", "<cmd>CMakeSelectKit<cr>", desc = "Select Kit" },
            { "<leader>mt", "<cmd>CMakeSelectBuildType<cr>", desc = "Select Build Type" },
            { "<leader>mT", "<cmd>CMakeSelectBuildTarget<cr>", desc = "Select Build Target" },
        },
    },
    {
        "folke/which-key.nvim",
        opts = {
            spec = {
                { "<leader>m", group = "cmake" },
            },
        },
    },
    {
        "mfussenegger/nvim-dap",
        optional = true,
        opts = function()
            local dap = require("dap")
            -- gdb 14+ speaks DAP itself, so no adapter needs downloading. It needs a gdb built with Python.
            dap.adapters.gdb = dap.adapters.gdb
                or function(callback, config)
                    callback({
                        type = "executable",
                        command = config.gdb or "gdb",
                        args = { "--interpreter=dap", "--eval-command", "set print pretty on" },
                    })
                end
            for _, lang in ipairs({ "c", "cpp" }) do
                dap.configurations[lang] = dap.configurations[lang] or {}
                table.insert(
                    dap.configurations[lang],
                    setmetatable({
                        name = "gdbserver: connect to target",
                        type = "gdb",
                        request = "attach",
                        cwd = "${workspaceFolder}",
                    }, { __call = connect_to_gdbserver })
                )
            end
        end,
    },
}
