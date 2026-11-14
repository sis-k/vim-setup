-- diffview+ (maintained fork of sindrets/diffview.nvim): changed-file panel, side-by-side diffs,
-- file history and a 3-way merge tool. Press g? inside a view for its keys.
return {
    {
        "dlyongemallo/diffview-plus.nvim",
        version = "*",
        cmd = {
            "DiffviewOpen",
            "DiffviewClose",
            "DiffviewToggleFiles",
            "DiffviewFocusFiles",
            "DiffviewRefresh",
            "DiffviewFileHistory",
            "DiffviewDiffFiles",
            "DiffviewMergeFiles",
            "DiffviewDiffDirs",
        },
        keys = {
            { "<leader>gv", "<cmd>DiffviewOpen<cr>", desc = "Diffview (working tree)" },
            { "<leader>gV", "<cmd>DiffviewFileHistory %<cr>", desc = "Diffview File History" },
            { "<leader>gV", ":DiffviewFileHistory<cr>", mode = "x", desc = "Diffview Line History" },
            { "<leader>gq", "<cmd>DiffviewClose<cr>", desc = "Diffview Close" },
        },
        opts = {
            enhanced_diff_hl = true,
        },
    },
}
