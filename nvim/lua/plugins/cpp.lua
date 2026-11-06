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
    local gdb_path = vim.fn.exepath(gdb)
    if gdb_path == "" then
        vim.notify(gdb .. " is not on PATH", vim.log.levels.ERROR)
        return vim.tbl_extend("force", config, { program = dap.ABORT })
    end
    return vim.tbl_extend("force", config, {
        program = vim.fn.fnamemodify(program, ":p"),
        miDebuggerServerAddress = target,
        miDebuggerPath = gdb_path,
    })
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
            -- Each kit and build type gets its own folder, because a CMake cache is tied to one toolchain.
            -- Presets set their own folder.
            cmake_build_directory = "build/${kit}/${variant:buildType}",
            cmake_kits_path = vim.fn.stdpath("config") .. "/cmake-kits.json",
            cmake_executor = { name = "overseer" },
        },
        keys = {
            { "<leader>mg", "<cmd>CMakeGenerate<cr>", desc = "Configure" },
            { "<leader>mG", ":CMakeGenerate ", desc = "Configure with Options" },
            { "<leader>mb", "<cmd>CMakeBuild<cr>", desc = "Build" },
            { "<leader>mc", "<cmd>CMakeClean<cr>", desc = "Clean" },
            { "<leader>mx", "<cmd>CMakeStopExecutor<cr>", desc = "Stop" },
            { "<leader>mp", "<cmd>CMakeSelectConfigurePreset<cr>", desc = "Select Configure Preset" },
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
        "mason-org/mason.nvim",
        opts = { ensure_installed = { "cpptools" } },
    },
    {
        "mfussenegger/nvim-dap",
        optional = true,
        opts = function()
            local dap = require("dap")
            -- cpptools drives gdb through MI. gdb's own DAP mode needs Python, which toolchain builds can lack.
            dap.adapters.cppdbg = dap.adapters.cppdbg
                or { id = "cppdbg", type = "executable", command = "OpenDebugAD7" }
            for _, lang in ipairs({ "c", "cpp" }) do
                dap.configurations[lang] = dap.configurations[lang] or {}
                table.insert(
                    dap.configurations[lang],
                    setmetatable({
                        name = "gdbserver: connect to target",
                        type = "cppdbg",
                        request = "launch",
                        MIMode = "gdb",
                        cwd = "${workspaceFolder}",
                        stopAtEntry = false,
                        setupCommands = {
                            { text = "-enable-pretty-printing", ignoreFailures = true },
                        },
                    }, { __call = connect_to_gdbserver })
                )
            end
        end,
    },
}
