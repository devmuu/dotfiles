local M = {}

-- define termcodes keys
local ESC = vim.api.nvim_replace_termcodes("<esc>", true, false, true)
local CLEAR = vim.api.nvim_replace_termcodes("<c-l>", true, false, true)
local ENTER = vim.api.nvim_replace_termcodes("<CR>", true, true, true)
local OUT_TERM = vim.api.nvim_replace_termcodes("<c-\\><c-n>", true, true, true)
local CLOSE_TERM = vim.api.nvim_replace_termcodes("<c-d>", true, true, true)
local LEFT_SPLIT = vim.api.nvim_replace_termcodes("<c-w><c-h>", true, true, true)
local RIGHT_SPLIT = vim.api.nvim_replace_termcodes("<c-w><c-l>", true, true, true)

-- define termcodes to nvim mode
local VISUAL = vim.api.nvim_replace_termcodes("v", true, false, true)
local NORMAL = vim.api.nvim_replace_termcodes("n", true, false, true)
local INSERT = vim.api.nvim_replace_termcodes("i", false, false, false)

-- open R console in vertical split
function OpenRTerminal()
    local bufnr = vim.api.nvim_create_buf(false, true)
    local opts = {
        split = "right",
        focusable = false,
        style = "minimal",
        anchor = "NE",
    }
    vim.api.nvim_open_win(bufnr, true, opts)

    local term = vim.fn.termopen({"R"}, {
        stdin = "pipe",
        pty = true,
    })

    -- save channel variable global to access from other functions
    channel = vim.bo.channel
    vim.api.nvim_chan_send(channel, "\n")
    vim.api.nvim_feedkeys(CLEAR, 'i', true)
    vim.api.nvim_feedkeys(OUT_TERM, 'n!', true)
    vim.api.nvim_feedkeys(LEFT_SPLIT, 'n', true)
end

-- send keys to a active terminal pane in nvim
function SendValue(mode)
    if mode == 0 then
        local r,c = table.unpack(vim.api.nvim_win_get_cursor(0))
        line_start = r
        line_end = r
        local res = vim.fn.getline(r, r)
        local r,c = table.unpack(vim.api.nvim_win_get_cursor(0))
        local lines = vim.fn.getline(r, r)
        vim.api.nvim_chan_send(channel, lines[1] .. "\n")

        local modeInfo = vim.api.nvim_get_mode()
        local current_mode = modeInfo.mode

        if current_mode ~= "n" then
            vim.api.nvim_feedkeys(ENTER, 'i', true)
        else
            vim.api.nvim_feedkeys('j', 'n', true)
        end

        print("Send to R terminal " .. channel)
    elseif mode == 1 then
        vim.api.nvim_chan_send(channel, CLEAR)
        vim.api.nvim_feedkeys(LEFT_SPLIT, 'n', true)
        print("R terminal clean")
    elseif mode == 2 then
        if channel ~= nil then
            vim.api.nvim_chan_send(channel, CLOSE_TERM)
            vim.api.nvim_feedkeys(RIGHT_SPLIT, 'n', true)
            vim.api.nvim_feedkeys('in', 'n', true)
            vim.api.nvim_feedkeys(ENTER, 'n', true)
            vim.api.nvim_feedkeys(LEFT_SPLIT, 'n', true)
            vim.api.nvim_feedkeys(ESC, 'n', true)
        else
            print("No channel.")
        end
        print("Exit R terminal")
    end
end

-- toggle backgroud
function toggle_background()
    local bg = vim.o.background

    if bg == 'light' then
        vim.api.nvim_set_option_value("background", "dark", {})
    else
        vim.api.nvim_set_option_value("background", "light", {})
    end
end

-- vim global to store cmp toggle flag
vim.g.cmp_toggle_flag = true

-- aux function
local normal_buftype = function()
    return vim.api.nvim_buf_get_option(0, "buftype") ~= "prompt"
end

-- toggle completion feature
function toggle_completion()
    local ok, cmp = pcall(require, "cmp")

    if ok then
        local next_cmp_toggle_flag = not vim.g.cmp_toggle_flag

        if next_cmp_toggle_flag then
            print("completion is on")
        else
            print("completion is off")
        end

        cmp.setup({
            enabled = function()
                vim.g.cmp_toggle_flag = next_cmp_toggle_flag

                if next_cmp_toggle_flag then
                    return normal_buftype
                else
                    return next_cmp_toggle_flag
                end
            end,
        })
    else
        print("completion not available")
    end
end

return M
