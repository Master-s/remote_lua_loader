-- TODO: Re-implement sceKernelSendNotificationRequest's logic with rop to support PS5 as well

sceKernelSendNotificationRequest__Address = nil
function check_is_ps4()
    if PLATFORM == "ps5" then
        error("This payload currently only works on PS4, but PS5 was selected.")
    end
end

function locate_notify()
    local libkernel_text = memory.read_buffer(libkernel_base, 0x40000)
    local matches = find_pattern(libkernel_text, "55 48 89 E5 41 57 41 56 41 54 53 49 89 F4")
    if matches and matches[1] ~= nil then
        sceKernelSendNotificationRequest__Address = libkernel_base:tonumber() + matches[1] - 1
        printf("sceKernelSendNotificationRequest address found: 0x%x\n", sceKernelSendNotificationRequest__Address)
    end
end

function sceKernelSendNotificationRequestFn(a1, buffer, size, a4)
    local sceKernelSendNotificationRequestAddr = function_rop(sceKernelSendNotificationRequest__Address)
    if sceKernelSendNotificationRequestAddr(a1, buffer, size, a4):tonumber() < 0 then
        error("sceKernelSendNotificationRequest() error: " .. get_error_string())
        return nil
    end
end

function sceKernelSendNotificationRequest(text)
    if sceKernelSendNotificationRequest__Address == nil then
        locate_notify()
    end
    if sceKernelSendNotificationRequest__Address ~= nil then
        local notify_buffer_size = 0xc30
        local notify_buffer = bump.alloc(notify_buffer_size)
        local icon_uri = "cxml://psnotification/tex_icon_system"

        -- credits to OSM-Made for this one. @ https://github.com/OSM-Made/PS4-Notify
        memory.write_dword(notify_buffer + 0, 0)            -- type
        memory.write_dword(notify_buffer + 0x28, 0)         -- unk3
        memory.write_dword(notify_buffer + 0x2C, 1)         -- use_icon_image_uri
        memory.write_dword(notify_buffer + 0x10, -1)        -- target_id
        memory.write_buffer(notify_buffer + 0x2D, text .. "\0") -- message
        memory.write_buffer(notify_buffer + 0x42D, icon_uri) -- uri
        sceKernelSendNotificationRequestFn(0, notify_buffer, notify_buffer_size, 0)
    end
end

function main()
    sceKernelSendNotificationRequest("Hello world")
end

check_is_ps4()
main()
