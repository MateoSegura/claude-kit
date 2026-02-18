# LSP and MCP Configuration — Complete Reference

This is the exhaustive specification for Language Server Protocol (`.lsp.json`) and Model Context Protocol (`.mcp.json`) configuration files in Claude Code plugins.

## .lsp.json — Language Server Protocol

LSP configuration gives Claude IDE-level language intelligence: diagnostics, go-to-definition, completions, hover info, and more. This makes Claude significantly more effective at understanding and navigating codebases.

### File Location

Place `.lsp.json` at the plugin root: `plugins/<name>/.lsp.json`

### Format

```json
{
  "server-name": {
    "command": "language-server-binary",
    "args": ["--flag1", "--flag2"],
    "extensionToLanguage": {
      ".ext": "language-id"
    }
  }
}
```

### All Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `command` | string | **yes** | The language server binary to run. Must be available on the system PATH or specified as an absolute path. |
| `extensionToLanguage` | object | **yes** | Maps file extensions to LSP language identifiers. The extension includes the dot (e.g., `".py"`). The language ID must match what the LSP server expects. |
| `args` | string[] | no | Command-line arguments passed to the server binary. |
| `transport` | string | no | Communication transport. Default is `"stdio"`. Options: `"stdio"`, `"tcp"`, `"pipe"`. |
| `env` | object | no | Environment variables set for the server process. Key-value pairs of strings. |
| `initializationOptions` | object | no | LSP initialization options sent to the server on startup. Server-specific — consult the server's documentation. |
| `settings` | object | no | LSP workspace settings. Equivalent to VS Code's `settings.json` entries for the language server. |
| `restartOnCrash` | boolean | no | Automatically restart the server if it crashes. Default is `false`. |

### Common Language Servers

| Language | Server | Command | Language ID |
|----------|--------|---------|-------------|
| C/C++ | clangd | `clangd` | `c`, `cpp` |
| Python | pyright | `pyright-langserver` | `python` |
| TypeScript/JavaScript | typescript-language-server | `typescript-language-server` | `typescript`, `javascript` |
| Rust | rust-analyzer | `rust-analyzer` | `rust` |
| Go | gopls | `gopls` | `go` |
| Java | jdtls | `jdtls` | `java` |
| C# | OmniSharp | `omnisharp` | `csharp` |
| Ruby | solargraph | `solargraph` | `ruby` |
| Lua | lua-language-server | `lua-language-server` | `lua` |
| Bash | bash-language-server | `bash-language-server` | `shellscript` |
| YAML | yaml-language-server | `yaml-language-server` | `yaml` |
| JSON | vscode-json-languageserver | `vscode-json-languageserver` | `json` |
| Zig | zls | `zls` | `zig` |
| Kotlin | kotlin-language-server | `kotlin-language-server` | `kotlin` |
| Swift | sourcekit-lsp | `sourcekit-lsp` | `swift` |

### Example: clangd for C/C++ (Embedded)

```json
{
  "clangd": {
    "command": "clangd",
    "args": [
      "--background-index",
      "--clang-tidy",
      "--header-insertion=iwyu",
      "--completion-style=detailed"
    ],
    "extensionToLanguage": {
      ".c": "c",
      ".h": "c",
      ".cpp": "cpp",
      ".hpp": "cpp",
      ".cc": "cpp"
    },
    "initializationOptions": {
      "clangdFileStatus": true
    }
  }
}
```

### Example: pyright for Python

```json
{
  "pyright": {
    "command": "pyright-langserver",
    "args": ["--stdio"],
    "extensionToLanguage": {
      ".py": "python",
      ".pyi": "python"
    },
    "settings": {
      "python": {
        "analysis": {
          "typeCheckingMode": "basic",
          "autoImportCompletions": true
        }
      }
    }
  }
}
```

### Example: rust-analyzer for Rust

```json
{
  "rust-analyzer": {
    "command": "rust-analyzer",
    "extensionToLanguage": {
      ".rs": "rust"
    },
    "settings": {
      "rust-analyzer": {
        "checkOnSave": {
          "command": "clippy"
        },
        "cargo": {
          "allFeatures": true
        }
      }
    },
    "restartOnCrash": true
  }
}
```

### Example: gopls for Go

```json
{
  "gopls": {
    "command": "gopls",
    "args": ["serve"],
    "extensionToLanguage": {
      ".go": "go",
      ".mod": "go.mod"
    },
    "settings": {
      "gopls": {
        "staticcheck": true,
        "gofumpt": true
      }
    }
  }
}
```

### Example: Multiple Servers (Multi-Language Project)

```json
{
  "clangd": {
    "command": "clangd",
    "args": ["--background-index"],
    "extensionToLanguage": {
      ".c": "c",
      ".cpp": "cpp",
      ".h": "c"
    }
  },
  "pyright": {
    "command": "pyright-langserver",
    "args": ["--stdio"],
    "extensionToLanguage": {
      ".py": "python"
    }
  },
  "yaml-language-server": {
    "command": "yaml-language-server",
    "args": ["--stdio"],
    "extensionToLanguage": {
      ".yaml": "yaml",
      ".yml": "yaml"
    }
  }
}
```

### Extension-to-Language Mapping

The `extensionToLanguage` field maps file extensions (including the dot) to LSP language identifiers. The language ID must exactly match what the language server expects.

Common mappings:

| Extension | Language ID | Notes |
|-----------|-------------|-------|
| `.c` | `c` | C source files |
| `.h` | `c` or `cpp` | Header files — use `c` for C-only projects |
| `.cpp`, `.cc`, `.cxx` | `cpp` | C++ source files |
| `.hpp`, `.hxx` | `cpp` | C++ header files |
| `.py` | `python` | Python source files |
| `.pyi` | `python` | Python type stub files |
| `.js` | `javascript` | JavaScript files |
| `.ts` | `typescript` | TypeScript files |
| `.jsx` | `javascriptreact` | JSX files |
| `.tsx` | `typescriptreact` | TSX files |
| `.rs` | `rust` | Rust source files |
| `.go` | `go` | Go source files |
| `.java` | `java` | Java source files |
| `.rb` | `ruby` | Ruby source files |
| `.lua` | `lua` | Lua source files |
| `.zig` | `zig` | Zig source files |
| `.sh`, `.bash` | `shellscript` | Shell scripts |
| `.json` | `json` | JSON files |
| `.yaml`, `.yml` | `yaml` | YAML files |
| `.toml` | `toml` | TOML files |
| `.md` | `markdown` | Markdown files |

### When to Include .lsp.json

Include `.lsp.json` whenever the domain has a widely-available language server:

- **Always include** for: C/C++ (clangd), Python (pyright), TypeScript (tsserver), Rust (rust-analyzer), Go (gopls)
- **Consider including** for: Java (jdtls), Ruby (solargraph), Kotlin, Swift
- **Skip** for: Domain-specific DSLs without LSP support, configuration-only plugins

### Tips

- Verify the language server binary is installed before relying on it — hooks can check this at SessionStart
- Use `restartOnCrash: true` for servers that may be unstable
- Keep `args` minimal — most servers work well with defaults
- The `settings` field mirrors VS Code workspace settings — consult VS Code extension docs for available options

---

## .mcp.json — Model Context Protocol

MCP configuration connects Claude to external tool servers, extending Claude's capabilities with custom tools, data sources, and integrations.

### File Location

Place `.mcp.json` at the plugin root: `plugins/<name>/.mcp.json`

### Format

```json
{
  "mcpServers": {
    "server-name": {
      "command": "command-to-start-server",
      "args": ["arg1", "arg2"],
      "env": {
        "ENV_VAR": "value"
      }
    }
  }
}
```

### All Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `command` | string | **yes** | The command to start the MCP server. Can be a binary name on PATH or an absolute path. |
| `args` | string[] | no | Arguments passed to the server command. |
| `env` | object | no | Environment variables set for the server process. Supports `${CLAUDE_PLUGIN_ROOT}` for plugin-relative paths. |
| `url` | string | no | For remote MCP servers, the URL to connect to (instead of `command`). |
| `transport` | string | no | Communication transport: `"stdio"` (default), `"sse"`, `"streamable-http"`. |

### Example: Node.js MCP Server

```json
{
  "mcpServers": {
    "custom-tools": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/mcp/server.js"],
      "env": {
        "DATA_DIR": "${CLAUDE_PLUGIN_ROOT}/data",
        "LOG_LEVEL": "info"
      }
    }
  }
}
```

### Example: Python MCP Server

```json
{
  "mcpServers": {
    "analysis-tools": {
      "command": "python3",
      "args": [
        "${CLAUDE_PLUGIN_ROOT}/mcp/analysis_server.py",
        "--port", "0"
      ],
      "env": {
        "PYTHONPATH": "${CLAUDE_PLUGIN_ROOT}/mcp"
      }
    }
  }
}
```

### Example: Remote MCP Server (SSE)

```json
{
  "mcpServers": {
    "cloud-tools": {
      "url": "https://mcp.example.com/sse",
      "transport": "sse"
    }
  }
}
```

### Example: Filesystem MCP Server

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@anthropic-ai/mcp-server-filesystem",
        "${CLAUDE_PLUGIN_ROOT}/data"
      ]
    }
  }
}
```

### Example: Multiple MCP Servers

```json
{
  "mcpServers": {
    "database": {
      "command": "python3",
      "args": ["${CLAUDE_PLUGIN_ROOT}/mcp/db_server.py"],
      "env": {
        "DB_PATH": "${CLAUDE_PLUGIN_ROOT}/data/project.db"
      }
    },
    "documentation": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/mcp/docs_server.js"],
      "env": {
        "DOCS_DIR": "${CLAUDE_PLUGIN_ROOT}/docs"
      }
    },
    "testing": {
      "command": "${CLAUDE_PLUGIN_ROOT}/mcp/test_server",
      "args": ["--watch"]
    }
  }
}
```

### Using ${CLAUDE_PLUGIN_ROOT}

Always use `${CLAUDE_PLUGIN_ROOT}` for paths within the plugin directory. This variable resolves to the plugin's absolute path at runtime, making the configuration portable.

```json
// CORRECT — portable
"command": "node",
"args": ["${CLAUDE_PLUGIN_ROOT}/mcp/server.js"]

// WRONG — hardcoded, breaks on other machines
"command": "node",
"args": ["/home/mateo/personal/agent-config/plugins/coding-embedded-zephyr-engineer/mcp/server.js"]
```

### Restricting MCP Server Access

You can limit which agents have access to specific MCP servers using the agent's `mcpServers` frontmatter field:

```yaml
# In the agent's frontmatter:
mcpServers: database, documentation
```

This is useful when some MCP servers provide sensitive capabilities that not all agents should access.

### When to Include .mcp.json

Include `.mcp.json` when:

- The domain requires external data sources (databases, APIs)
- Custom tools are needed beyond Claude's built-in tools
- Integration with external services is part of the workflow
- Domain-specific analysis tools are available as MCP servers

### MCP vs LSP

| Aspect | MCP (.mcp.json) | LSP (.lsp.json) |
|--------|-----------------|-----------------|
| Purpose | External tools and data | Language intelligence |
| Protocol | Model Context Protocol | Language Server Protocol |
| Provides | Custom tools, data access | Diagnostics, completions, go-to-def |
| When to use | Custom capabilities needed | Language has an available server |
| Overhead | Depends on server | Minimal for most servers |

---

## Combined Example: Plugin with Both LSP and MCP

For a Zephyr RTOS embedded development plugin:

### .lsp.json

```json
{
  "clangd": {
    "command": "clangd",
    "args": [
      "--background-index",
      "--clang-tidy",
      "--query-driver=/opt/zephyr-sdk/*/bin/*-gcc"
    ],
    "extensionToLanguage": {
      ".c": "c",
      ".h": "c",
      ".cpp": "cpp"
    }
  },
  "pyright": {
    "command": "pyright-langserver",
    "args": ["--stdio"],
    "extensionToLanguage": {
      ".py": "python"
    }
  }
}
```

### .mcp.json

```json
{
  "mcpServers": {
    "zephyr-docs": {
      "command": "python3",
      "args": ["${CLAUDE_PLUGIN_ROOT}/mcp/zephyr_docs_server.py"],
      "env": {
        "ZEPHYR_BASE": "/opt/zephyr",
        "DOCS_INDEX": "${CLAUDE_PLUGIN_ROOT}/data/docs-index.json"
      }
    }
  }
}
```

This configuration gives Claude:
- **clangd**: C/C++ diagnostics, completions, and navigation for Zephyr kernel code
- **pyright**: Python intelligence for West build scripts and test harnesses
- **zephyr-docs**: Custom MCP server providing Zephyr API documentation lookup
