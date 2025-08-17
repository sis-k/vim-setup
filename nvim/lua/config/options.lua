-- Options are automatically loaded before lazy.nvim startup
-- Default options that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/options.lua
-- Add any additional options here
--
-- Spaces
vim.opt.shiftwidth = 4 -- Size of an indent
vim.opt.tabstop = 4 -- size of tabstop

-- Leader keys etc.
vim.g.mapleader = " "
vim.g.maplocalleader = "\\"

-- LazyVim auto format
vim.g.autoformat = false

-- Disble diagnostic by default
vim.diagnostic.enable(false)

vim.opt.exrc = true
