local OS_NAME = vim.loop.os_uname().sysname

-- load mappings
require("mappings")

-- load lazy plugin manager
require("lazy_init")

-- load settings
require("settings")

-- load user module
require("user")
