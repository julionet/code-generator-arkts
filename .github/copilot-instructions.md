# AI Coding Agent Instructions for code-generator-arkts

## Project Overview
**code-generator-arkts** generates ArkTS (Harmony OS) code following Clean Architecture or MVVM patterns. It's a Python CLI tool that takes entity definitions and produces production-ready layered architecture code with optional validation and local caching.

## Architecture & Data Flow

### Core Design Pattern: Template-Based Code Generation
The generator operates on a **configuration → generation → file writing** pipeline:

1. **Input**: `GeneratorConfig` dataclass with entity name, properties, and feature flags
2. **Generation**: `CodeGenerator` class has separate `_generate_*()` methods for each file type
3. **Output**: Dictionary mapping file paths to string content, written to disk atomically

### Two Architecture Modes

#### Clean Architecture (default)
Generates 10+ files across **domain/data/presentation** layers:
- **Domain Layer**: Entity classes with validation, repository interfaces, use cases
- **Data Layer**: DTOs, mappers, remote/local datasources, repository implementations  
- **Presentation Layer**: ViewModels, Pages

Example flow for "User" entity:
```
User (domain/entities/)
  ↓ implements
I{Entity}Repository (domain/repositories/)
  ↓ called by
Get{Entities}UseCase (domain/usecases/)
  ↓ uses
{Entity}Mapper to/from DTO (data/models/)
  ↓ fetches from
{Entity}RemoteDataSourceImpl (data/datasources/)
```

#### MVVM Mode
Simplified generation: Model → Repository → ViewModel → Page (4 files)

### Key Technical Decisions

1. **Entity.copy()** method enables immutability pattern for clean architecture
2. **PropertyConfig.optional** flag controls TypeScript `?` operator and validation
3. **ValidationRule** dataclass allows composable validation logic per property
4. **Mapper pattern** separates domain entities from DTO serialization (handles Date conversion)
5. **Pluralization** (via `_pluralize()`) generates correct endpoint paths and method names

## Developer Workflows

### CLI Usage Patterns
```bash
# Clean Architecture with features
python -m cli.py generate User --props "id:number,name:string" --cache --validation --arch clean

# MVVM simple
python -m cli.py g Product --props "name:string,price:number" --arch mvvm

# Interactive mode (stub for future enhancement)
python -m cli.py interactive
```

### Testing the Generator
1. Run `example_usage.py` to generate sample outputs into `./examples/` directories
2. Inspect generated files in three example configs: User (clean+validation), Product (mvvm), BlogPost (clean)

## Code Organization & Patterns

### Generator Methods Pattern
Each `_generate_*()` method:
- Returns a complete ArkTS file as a formatted string
- Uses f-strings with proper indentation via `_indent_code()`
- Includes file path as comment (e.g., `// domain/entities/User.ets`)
- Handles optional features (cache, validation) via config flags

### Property Processing
```python
# Pattern: iterate config.properties and generate code
for prop in self.config.properties:
    optional = '?' if prop.optional else ''
    lines.append(f"public {prop.name}{optional}: {prop.type};")
```

### Entity Construction Pattern
- **Constructor**: Public params for each property (immutability via const assignment)
- **Validation**: Optional `validate()` called in constructor if `include_validation=True`
- **Serialization**: `toJson()`, `fromJson()` static method, plus `copy()` for updates

### Use Case Pattern
- Single responsibility: one use case per CRUD operation
- Constructor injection of repository interface
- `execute()` method with typed parameters and return
- Validation of ID values (> 0 check in GetById, Delete)

## Integration Points & Dependencies

### External Dependencies
- `aiohttp` & `aiofiles`: Async I/O (requirements.txt) — **not yet used in generation**, likely for future file writing
- `argparse`: CLI argument parsing
- `typing-extensions`: Type hints compatibility

### Generated Code Dependencies
Generated ArkTS files depend on:
- `@ohos.net.http`: Network requests (RemoteDataSourceImpl)
- `@harmony` ecosystem: Date handling, Promise support
- AppContainer injection pattern (mentioned in CLI output)

### Configuration Points for Generated Code
- **BaseURL in datasources**: Default `https://api.example.com` — must be configured post-generation
- **AppContainer**: User must register repositories and use cases (mentioned in next steps)
- **Endpoint naming**: Assumes REST endpoint format `/{entity_plural}` (e.g., `/users`, `/products`)

## Project-Specific Conventions

### Naming Conventions
- **Entity names**: PascalCase (User, BlogPost)
- **Properties**: camelCase (firstName, createdAt)
- **Pluralization rules**: English rules via `_pluralize()` (user→users, category→categories, class→classes)
- **Interface prefixes**: `I` for all interfaces (IUserRepository, IUserRemoteDataSource)

### ArkTS Code Style in Generation
- Async/await for all network operations
- Const assertion for readonly properties (id fields)
- Arrow functions in mappers and data transformations
- Generic types `<T>` for request/response wrappers
- Date ISO string conversion for JSON serialization

### Validation Patterns
Only generated if `include_validation=True`:
- **REQUIRED**: Checks null/undefined/empty for strings
- **MIN_LENGTH, MAX_LENGTH**: String length validation
- **EMAIL**: Regex pattern validation
- **MIN, MAX**: Numeric range validation
- **PATTERN**: Custom regex from rule.value
- Messages customizable per rule or auto-generated

## Testing & Validation Guidelines

### What to Test When Modifying Generator
1. **Property mapping**: Ensure all config.properties appear in generated code
2. **Method signatures**: Use cases should accept correct types in `execute()`
3. **File paths**: Generated paths must match Clean/MVVM folder structures
4. **Pluralization edge cases**: Test `category`, `status`, `class` (edge cases handled by `_pluralize()`)
5. **Optional properties**: `PropertyConfig.optional=True` should appear as `?` in all generated code
6. **Validation logic**: Regenerate with/without `include_validation` flag and inspect entity constructor

### Example Verification Flow
```python
# Verify generated mapper handles Date correctly
config = GeneratorConfig(
    entity_name="Event",
    properties=[PropertyConfig(name="startDate", type="Date")]
)
generated = CodeGenerator(config)._generate_model()
assert "new Date(json.startDate)" in generated  # Check fromJson mapping
```

## Common Modification Points

### Adding a New Generation Feature
1. Add flag to `GeneratorConfig` dataclass (e.g., `include_dto_validation: bool = False`)
2. Add conditional in `generate_all()` to include new files if flag is True
3. Implement new `_generate_new_feature()` method with full ArkTS template
4. Update CLI argument parser in `GeneratorCLI.run()` if user-facing

### Extending Validation Types
1. Add new enum value to `ValidationType`
2. Add handling in `_generate_validations()` with conditional block
3. Add test case in `example_usage.py`

### Changing Output Directory Structure
Modify file path strings in `generate_all()` — e.g., change `"domain/entities/"` to `"src/domain/entities/"`
