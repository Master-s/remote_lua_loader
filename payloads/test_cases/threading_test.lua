
function test_print()

    local lua_code = [[

        function main()

            syscall.resolve({
                thr_self = 432
            })

            local tid = memory.alloc(8)
            syscall.thr_self(tid)
            tid = memory.read_qword(tid)

            print()
            print("hello world from thread!")
            print("thread id: " .. hex(tid))
        end

        main()
    ]]

    run_lua_code_in_new_thread(lua_code, { client_fd = client_fd })
end

function test_syntax_error()
    run_lua_code_in_new_thread("`", { client_fd = client_fd })
end

function test_runtime_error()

    local lua_code = [[
        function main()
            tbl.notexist()
        end
        main()
    ]]

    run_lua_code_in_new_thread(lua_code, { client_fd = client_fd })
end

function test_write_from_thread()

    local mem = memory.alloc(8)
    memory.write_qword(mem, 0xdead)
    
    local lua_code = [[
        function main()
            sleep(1)
            memory.write_qword(args.addr, 0x1337)
        end
        main()
    ]]

    local thr = run_lua_code_in_new_thread(lua_code, {
        async = true,
        client_fd = client_fd,
        args = {
            addr = mem
        }
    })

    print()
    print("before write from new thread: " .. hex(memory.read_qword(mem)))
    print("sleeping for few seconds before checking again...")
    sleep(2)
    print("after write from new thread: " .. hex(memory.read_qword(mem)))
end

function test_high_contentions()

    local lua_code = [[

        local Atomic_fetch_add_8 = fcall(libc_addrofs.Atomic_fetch_add_8)

        function main()
            for i=1,0x10 do
                Atomic_fetch_add_8(args.number, 1)
            end
        end

        main()
    ]]

    local thr_count = 4 -- high chance to crash with large value
    local thr_list = {}

    local number = memory.alloc(8)

    for i=1,thr_count do
        local thr = run_lua_code_in_new_thread(lua_code, {
            async = true,
            client_fd = client_fd,
            args = {
                number = number,
            }
        })
        table.insert(thr_list, thr)
    end

    for i,thr in ipairs(thr_list) do
        thr:join()
    end

    print("number = " .. hex(memory.read_dword(number)))
end

function main()
    test_print()
    -- test_syntax_error()
    -- test_runtime_error()
    -- test_write_from_thread()
    -- test_high_contentions()
end

main()