# CMake Patterns for Zephyr

## Zephyr Library Pattern

```cmake
zephyr_library()
zephyr_library_sources(
    src/file1.c
    src/file2.c
)
zephyr_library_include_directories(include/)
zephyr_library_compile_definitions(MY_DEFINE=1)
```

## Target Sources Pattern

```cmake
target_sources(app PRIVATE
    src/main.c
    src/module.c
)
```

## Conditional Sources

```cmake
target_sources_ifdef(CONFIG_FEATURE app PRIVATE src/feature.c)
```

## Generator Expressions

```cmake
target_compile_definitions(app PRIVATE
    $<$<CONFIG:RELEASE>:NDEBUG>
    $<$<CONFIG:DEBUG>:DEBUG_MODE>
)
```

## External Libraries

```cmake
add_library(mylib STATIC IMPORTED)
set_target_properties(mylib PROPERTIES
    IMPORTED_LOCATION ${CMAKE_CURRENT_SOURCE_DIR}/lib/libmylib.a
    INTERFACE_INCLUDE_DIRECTORIES ${CMAKE_CURRENT_SOURCE_DIR}/lib/include
)
target_link_libraries(app PRIVATE mylib)
```

## Zephyr Module CMakeLists.txt

```cmake
zephyr_library_named(mymodule)
zephyr_library_sources(module.c)
zephyr_library_include_directories(.)
```

**Kconfig:**

```kconfig
config MYMODULE
    bool "My Module"
    default y
```
