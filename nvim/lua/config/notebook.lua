-- Read-only .ipynb viewer, script export and JupyterLab launcher. Needs only uv.
-- Loaded from init.lua, because the VeryLazy event is too late for `nvim file.ipynb`.
local JUPYTEXT = {
    "uvx",
    "jupytext",
    "--to",
    "py:percent",
    "--opt",
    "notebook_metadata_filter=-all",
    "--opt",
    "cell_metadata_filter=-all",
}

local function to_python(path, output)
    local cmd = vim.list_extend(vim.deepcopy(JUPYTEXT), { "--output", output, path })
    return vim.system(cmd, { text = true }):wait()
end

-- Show notebooks as Python. The buffer has no file behind it, so :w cannot touch the notebook.
vim.api.nvim_create_autocmd("BufReadCmd", {
    group = vim.api.nvim_create_augroup("notebook_view", { clear = true }),
    pattern = "*.ipynb",
    callback = function(args)
        local result = to_python(vim.api.nvim_buf_get_name(args.buf), "-")
        local text = result.code == 0 and result.stdout or ("jupytext failed:\n" .. result.stderr)
        vim.bo[args.buf].modifiable = true -- :edit reloads into a buffer that is already read-only
        vim.api.nvim_buf_set_lines(args.buf, 0, -1, false, vim.split(text, "\n", { trimempty = true }))
        vim.bo[args.buf].buftype = "nofile"
        vim.bo[args.buf].swapfile = false
        vim.bo[args.buf].modifiable = false
        vim.bo[args.buf].filetype = "python"
        -- BufReadCmd replaces the read, so this event doesn't fire by itself. LazyVim's file plugins wait for it.
        vim.api.nvim_exec_autocmds("BufReadPost", { buffer = args.buf, modeline = false })
    end,
})

-- :NbScript [path] writes a script next to the notebook, or to path, and never overwrites a file.
vim.api.nvim_create_user_command("NbScript", function(opts)
    local notebook = vim.api.nvim_buf_get_name(0)
    if not notebook:match("%.ipynb$") then
        return vim.notify("Not a notebook", vim.log.levels.ERROR)
    end
    local target = opts.args ~= "" and vim.fn.fnamemodify(opts.args, ":p") or notebook:gsub("%.ipynb$", ".py")
    if vim.uv.fs_stat(target) then
        return vim.notify(target .. " already exists; use :NbScript <path>", vim.log.levels.ERROR)
    end
    local result = to_python(notebook, target)
    if result.code ~= 0 then
        return vim.notify(result.stderr, vim.log.levels.ERROR)
    end
    vim.cmd.edit(vim.fn.fnameescape(target))
end, { nargs = "?", complete = "file" })

-- :NbServe starts JupyterLab from the project root and it opens the browser. Running it again reopens the page.
-- :NbStop stops the server, and it also stops when Neovim exits.
local server, url, stopping
vim.api.nvim_create_user_command("NbServe", function()
    if server then
        if url then
            vim.ui.open(url)
        else
            vim.notify("JupyterLab is still starting")
        end
        return
    end
    local root = vim.fs.root(0, { "pyproject.toml", ".git" }) or vim.uv.cwd()
    vim.notify("Starting JupyterLab in " .. root)
    local log = {}
    -- The redirect page is a local HTML file, which can open in a different browser from http links.
    local cmd = { "uv", "run", "--with", "jupyterlab", "jupyter", "lab", "--ServerApp.use_redirect_file=False" }
    server = vim.fn.jobstart(cmd, {
        cwd = root,
        stderr_buffered = false,
        on_stderr = function(_, lines)
            vim.list_extend(log, lines)
            for _, line in ipairs(lines) do
                url = url or line:match("http://localhost:%d+/lab%?token=%w+")
            end
        end,
        on_exit = function(_, code)
            local stopped = stopping
            server, url, stopping = nil, nil, nil
            if vim.v.exiting ~= vim.NIL then
                return
            end
            vim.schedule(function()
                if stopped then
                    vim.notify("JupyterLab stopped")
                elseif code ~= 0 then
                    vim.notify(
                        "JupyterLab exited:\n" .. table.concat(log, "\n", math.max(1, #log - 10)),
                        vim.log.levels.ERROR
                    )
                end
            end)
        end,
    })
end, {})

vim.api.nvim_create_user_command("NbStop", function()
    if not server then
        return vim.notify("JupyterLab isn't running")
    end
    stopping = true
    vim.fn.jobstop(server)
end, {})

vim.keymap.set("n", "<leader>je", "<cmd>NbScript<cr>", { desc = "Export Notebook to Script" })
vim.keymap.set("n", "<leader>js", "<cmd>NbServe<cr>", { desc = "Serve Notebooks (JupyterLab)" })
vim.keymap.set("n", "<leader>jq", "<cmd>NbStop<cr>", { desc = "Stop Notebook Server" })
