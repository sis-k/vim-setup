return {
    {
        "EthanJWright/vs-tasks.nvim",
        dependencies = {
            "nvim-lua/popup.nvim",
            "nvim-lua/plenary.nvim",
            "folke/snacks.nvim",
        },
        opts = {
            picker = "snacks" -- Use snacks.nvim picker instead of telescope
        },
        config = function ()
        end
    }
}
