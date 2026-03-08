syntax on
set number
set listchars=tab:>·,trail:~,extends:>,precedes:<
set list
set path+=**
colorscheme desert
set expandtab
set tabstop=4
set shiftwidth=4
set autoindent
filetype plugin indent on

" YouCompleteMe
packadd YouCompleteMe
let g:ycm_autoclose_preview_window_after_completion=1
map <leader>g  :YcmCompleter GoToDefinitionElseDeclaration<CR>

" Enable folding
set foldmethod=indent
set foldlevel=99
" Enable folding with the spacebar
nnoremap <space> za

set encoding=utf-8
map <C-F>      :FZF<CR>

map <C-S>      :w<CR>
map <C-Q>      :q!<CR>
map <C-T>      :tabnew<CR>
map <C-N>      :NERDTreeFind<CR>
map <C-M>      :NERDTreeToggle<CR>
map <C-Down>   :tabnext<CR>
map <C-Up>     :tabprevious<CR>

nmap <C-B>     :Buffers<CR>
nmap <S-F>     :RG<CR>

" shift+arrow selection
nmap <S-Up> v<Up>
nmap <S-Down> v<Down>
nmap <S-Left> v<Left>
nmap <S-Right> v<Right>
vmap <S-Up> <Up>
vmap <S-Down> <Down>
vmap <S-Left> <Left>
vmap <S-Right> <Right>
imap <S-Up> <Esc>v<Up>
imap <S-Down> <Esc>v<Down>
imap <S-Left> <Esc>v<Left>
imap <S-Right> <Esc>v<Right>

vmap <C-c> y<Esc>i
vmap <C-x> d<Esc>i
vmap <C-v> pi
imap <C-v> <Esc>pi
imap <C-z> <Esc>ui

