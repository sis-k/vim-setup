-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here
local map = vim.keymap.set

map("n", "<leader><Left>", "<C-w>h", { desc = "Go to Left Window", remap = true })
map("n", "<leader><Right>", "<C-w>l", { desc = "Go to Right Window", remap = true })
map("n", "<leader><Down>", "<C-w>j", { desc = "Go to Upper Window", remap = true })
map("n", "<leader><Up>", "<C-w>k", { desc = "Go to Lower Window", remap = true })

-- Copilot
vim.keymap.set("n", "<leader>cp", ":Copilot panel<cr>")
vim.keymap.set("n", "<leader>cs", ":Copilot status<cr>")

-- Resize window using <ctrl> hjkl keys
-- map("n", "<C-j>", "<cmd>resize +2<cr>", { desc = "Increase Window Height" })
-- map("n", "<C-k>", "<cmd>resize -2<cr>", { desc = "Decrease Window Height" })
-- map("n", "<C-h>", "<cmd>vertical resize -2<cr>", { desc = "Decrease Window Width" })
-- map("n", "<C-l>", "<cmd>vertical resize +2<cr>", { desc = "Increase Window Width" })

-- -- Move to window using the <ctrl> and arrow keys
-- map("n", "<C-Left>", "<C-w>h", { desc = "Go to Left Window", remap = true })
-- map("n", "<C-Right>", "<C-w>l", { desc = "Go to Right Window", remap = true })
-- map("n", "<C-Down>", "<C-w>j", { desc = "Go to Upper Window", remap = true })
-- map("n", "<C-Up>", "<C-w>k", { desc = "Go to Lower Window", remap = true })

map("n", "<S-PageUp>", "<cmd>bprevious<cr>", { desc = "Prev Buffer" })
map("n", "<S-PageDown>", "<cmd>bnext<cr>", { desc = "Next Buffer" })

map("n", "W", "vaw", { desc = "Select the current word" })
map("n", "Y", "yaw", { desc = "Yank the current word" })

map("i", "<S-Up>", "<esc>v<Up>", { desc = "Select text up" })
map("i", "<S-Down>", "<esc>v<Down>", { desc = "Select text down" })
map("i", "<S-Left>", "<esc>v<Left>", { desc = "Select text left" })
map("i", "<S-Right>", "<esc>v<Right>", { desc = "Select text right" })

map("n", "<leader>os", ":OverseerShell<cr>", { desc = "Overseer shell" })
map("n", "<leader>or", ":OverseerRun<cr>", { desc = "Overseer run" })

-- File operations
vim.api.nvim_create_user_command("CopyFullPath", function()
    local path = vim.fn.expand("%:p")
    vim.fn.setreg("+", path)
end, {})
vim.keymap.set("n", "<leader>cf", ":CopyFullPath<cr>")

vim.api.nvim_create_user_command("CopyRelativePath", function()
    local path = vim.fn.expand("%:.")
    vim.fn.setreg("+", path)
end, {})
vim.keymap.set("n", "<leader>cF", ":CopyRelativePath<cr>")
