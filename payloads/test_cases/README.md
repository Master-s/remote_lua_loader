
### Test Payloads

| Payload | Description |
| -------- | ------- |
| sigsegv_crash_trigger.lua | Triggers two SIGSEGV crashes in succession that should be signal handled without crashing the game process. |
| notification_popup.lua | Triggers a notification popup with 'Hello World' on the PlayStation. |
| sigbus_crash_trigger.lua | Triggers a SIGBUS crash that should be signal handled without crashing the game process. |
| streaming_output.lua | Prints basic information and trigger two SIGSEGV crashes in the middle, to demonstrate how streaming real-time output works. |
| threading_test.lua | Provides examples on how to run lua code in new threads. |
