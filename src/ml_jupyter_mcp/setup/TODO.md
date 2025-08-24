# Setup Module TODO

## Project Setup Functionality

### Core Implementation
- [ ] Create `project_setup.py` with main setup logic
- [ ] Create `templates.py` to store default `.mcp.json` and `CLAUDE.md` templates
- [ ] Implement smart merge functionality for existing `.mcp.json` files
- [ ] Implement append functionality for existing `CLAUDE.md` files

### File Handlers
- [ ] `.mcp.json` handler:
  - Detect existing file
  - Merge jupyter-executor config without duplication
  - Preserve existing user configurations
  - Handle nested JSON structures properly

- [ ] `CLAUDE.md` handler:
  - Detect existing file
  - Append jupyter-specific instructions if not present
  - Avoid duplicate sections
  - Maintain markdown formatting

### MCP Tool Integration
- [ ] Create `jupyter_setup_project()` tool
- [ ] Add parameters:
  - `project_path` (default: current directory)
  - `override_existing` (default: False)
  - `custom_config` (optional: Dict for custom settings)
- [ ] Return setup status and warnings

### CLI Integration
- [ ] Add CLI command: `ml-jupyter-mcp setup [path]`
- [ ] Add `--force` flag for overwriting
- [ ] Add `--check` flag to verify setup without changes

### Templates
- [ ] Default `.mcp.json` template with:
  - jupyter-executor configuration
  - Workflow instructions
  - Cell execution patterns
  - Error handling rules

- [ ] Default `CLAUDE.md` template with:
  - Jupyter workflow instructions
  - Cell execution patterns
  - Package management guidelines
  - Error handling procedures

### Testing
- [ ] Test fresh setup in empty project
- [ ] Test merging with existing `.mcp.json`
- [ ] Test appending to existing `CLAUDE.md`
- [ ] Test duplicate prevention
- [ ] Test CLI commands
- [ ] Test MCP tool usage

### Documentation
- [ ] Update README with setup instructions
- [ ] Add docstrings to all functions
- [ ] Create setup examples
- [ ] Document merge behavior

### Edge Cases
- [ ] Handle malformed existing JSON
- [ ] Handle read-only files
- [ ] Handle missing permissions
- [ ] Handle symbolic links
- [ ] Handle very large existing files

## Implementation Priority
1. Basic file creation for new projects
2. Smart merge for `.mcp.json`
3. Smart append for `CLAUDE.md`
4. MCP tool integration
5. CLI command
6. Testing
7. Documentation