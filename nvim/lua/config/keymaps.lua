-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here
local map = vim.keymap.set

map("n", "<leader><Left>", "<C-w>h", { desc = "Go to Left Window", remap = true })
map("n", "<leader><Right>", "<C-w>l", { desc = "Go to Right Window", remap = true })
map("n", "<leader><Down>", "<C-w>j", { desc = "Go to Upper Window", remap = true })
map("n", "<leader><Up>", "<C-w>k", { desc = "Go to Lower Window", remap = true })

map("n", "<S-PageUp>", "<cmd>bprevious<cr>", { desc = "Prev Buffer" })
map("n", "<S-PageDown>", "<cmd>bnext<cr>", { desc = "Next Buffer" })

map("n", "W", "vaw", { desc = "Select the current word" })
map("n", "Y", "yaw", { desc = "Yank the current word" })

map("i", "<S-Up>", "<esc>v<Up>", { desc = "Select text up" })
map("i", "<S-Down>", "<esc>v<Down>", { desc = "Select text down" })
map("i", "<S-Left>", "<esc>v<Left>", { desc = "Select text left" })
map("i", "<S-Right>", "<esc>v<Right>", { desc = "Select text right" })

