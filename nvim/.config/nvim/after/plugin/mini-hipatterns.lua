local hipatterns = require('mini.hipatterns')

-- define group function to highlight hsl colors
local get_hsl = function(_, match)
    local utils = require("eletro-colors").hsl
    local hsl = utils.hslToHex
    local nh, ns, nl = match:match("hsl%((%d+),? (%d+),? (%d+)%)")
    local h, s, l = tonumber(nh), tonumber(ns), tonumber(nl)
    local hex_color = hsl(h, s, l)
    return MiniHipatterns.compute_hex_color_group(hex_color, "bg")
end

-- define group function to highlight latex hex color
local get_latex_hex = function(_, match)
    local c = match:match("%{HTML%}%{(%w+)%}")
    local hex_color =  "#" .. c
    return MiniHipatterns.compute_hex_color_group(hex_color, "bg")
end

-- define group function to highlight latex rgb color
local get_latex_rgb = function(_, match)
    local utils = require("eletro-colors").rgb
    local hex = utils.rgbToHex
    local r, g, b = match:match("%{RGB%}%{(%d+),? ?(%d+),? ?(%d+)%}")
    local value = {r, g, b}
    local hex_color =  hex(value)
    return MiniHipatterns.compute_hex_color_group(hex_color, "bg")
end

return {
    hipatterns.setup({
        highlighters = {
            -- Highlight standalone 'FIXME', 'HACK', 'TODO', 'NOTE'
            fixme = { pattern = '%f[%w]()FIXME()%f[%W]', group = 'MiniHipatternsFixme' },
            hack = { pattern = '%f[%w]()HACK()%f[%W]', group = 'MiniHipatternsHack' },
            todo = { pattern = '%f[%w]()TODO()%f[%W]', group = 'MiniHipatternsTodo' },
            note = { pattern = '%f[%w]()NOTE()%f[%W]', group = 'MiniHipatternsNote' },

            -- Highlight custom
            description = { pattern = '%f[%w]()DESCRIPTION()%f[%W]', group = 'Special' },
            program = { pattern = '%f[%w]()PROGRAM()%f[%W]', group = 'Special' },
            software = { pattern = '%f[%w]()SOFTWARE()%f[%W]', group = 'Todo' },

            -- Highlight hex color strings (`#rrggbb`) using that color
            hex_color = hipatterns.gen_highlighter.hex_color(),

            -- Highlight hsl color strings `hsl(h, s, l)` using that color
            hsl_color = { pattern = "hsl%(%d+,? %d+,? %d+%)", group = get_hsl },

            -- Highlight hex color strings in latex
            latex_hex_color = { pattern = "%{HTML%}%{%w+%}", group = get_latex_hex },

            -- Highlight rgb color strings in latex
            latex_rgb_color = { pattern = "%{RGB%}%{%d+,? ?%d+,? ?%d+%}", group = get_latex_rgb },
        },
    })
}
