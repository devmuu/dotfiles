function on_pause_change(name, value)
    if value == true then
        -- mp.set_property("fullscreen", "yes")
    end
end
mp.observe_property("pause", "bool", on_pause_change)

function something_handler(name, value)
    print("the key was pressed")
    ov = mp.create_osd_overlay("ass-events")
    ov.data = "{\\an5}{\\b1}hello world!"
    ov:update()
end
mp.add_key_binding("b", "something", something_handler)

local enabled = false
mp.add_key_binding('F2', function ()
    mp.commandv('script-message', 'osc-playlist', enabled and 0 or 999)
    enabled = not enabled
end)
