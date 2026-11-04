-- Run the debugpy adapter through uvx so it does not depend on a venv tied to the
-- system Python (see bin/debugpy-adapter). dap-python still runs the program being
-- debugged on the project's interpreter: $VIRTUAL_ENV, $CONDA_PREFIX, or a venv folder.
return {
    {
        "mfussenegger/nvim-dap-python",
        config = function()
            require("dap-python").setup(vim.fn.stdpath("config") .. "/bin/debugpy-adapter")
        end,
    },
}
