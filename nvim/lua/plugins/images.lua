-- Inline image rendering via the kitty graphics protocol (snacks.nvim image module).
-- Requires: kitty (or Ghostty/WezTerm) and ImageMagick (`brew install imagemagick`).
-- Optional: ghostscript (PDF), tectonic (LaTeX math), and mermaid-cli (`mmdc`, renders ```mermaid blocks and .mmd files;
-- it downloads a headless Chromium).
-- Inline markdown images need conceallevel >= 2, set below for markdown only when the terminal supports images
-- (otherwise it would just hide link syntax). Run `:checkhealth snacks` to see if the terminal is detected.
-- Under tmux: `set -g allow-passthrough on`.
return {
    {
        "folke/snacks.nvim",
        opts = {
            image = {
                enabled = true,
                -- Snacks caps inline images at 80x40 cells by default, which shrinks tall diagrams.
                -- The window size still limits the image, so these are only upper bounds.
                doc = { max_width = 200, max_height = 120 },
            },
        },
    },
    {
        "LazyVim/LazyVim",
        init = function()
            vim.api.nvim_create_autocmd("FileType", {
                pattern = { "markdown" },
                callback = function()
                    local ok, supported = pcall(function()
                        return Snacks.image.supports_terminal()
                    end)
                    if ok and supported then
                        vim.opt_local.conceallevel = 2
                    end
                end,
            })
        end,
    },
}
