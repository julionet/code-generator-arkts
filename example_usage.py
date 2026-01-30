# example_usage.py

"""
Exemplos de uso do Code Generator ArkTS
"""

from code_generator import (
    CodeGenerator,
    GeneratorConfig,
    PropertyConfig,
    ValidationRule,
    ValidationType
)
from pathlib import Path


def example_clean_architecture_with_validation():
    """Exemplo: Clean Architecture com validações completas"""
    print("📝 Exemplo 1: Clean Architecture com Validações")
    
    config = GeneratorConfig(
        entity_name="User",
        properties=[
            PropertyConfig(name="id", type="number"),
            PropertyConfig(
                name="name",
                type="string",
                validation=[
                    ValidationRule(ValidationType.REQUIRED, message="Nome é obrigatório"),
                    ValidationRule(ValidationType.MIN_LENGTH, value=3, message="Nome muito curto")
                ]
            ),
            PropertyConfig(
                name="email",
                type="string",
                validation=[
                    ValidationRule(ValidationType.REQUIRED),
                    ValidationRule(ValidationType.EMAIL)
                ]
            ),
            PropertyConfig(
                name="age",
                type="number",
                optional=True,
                validation=[
                    ValidationRule(ValidationType.MIN, value=0),
                    ValidationRule(ValidationType.MAX, value=150)
                ]
            ),
            PropertyConfig(name="createdAt", type="Date")
        ],
        include_cache=True,
        include_validation=True,
        architecture='clean'
    )
    
    generator = CodeGenerator(config)
    files = generator.generate_all()
    
    # Salva arquivos
    output_dir = Path("./examples/user_clean")
    _save_files(files, output_dir)
    
    print(f"✅ {len(files)} arquivos gerados em {output_dir}\n")


def example_mvvm_simple():
    """Exemplo: MVVM Tradicional simples"""
    print("📝 Exemplo 2: MVVM Tradicional")
    
    config = GeneratorConfig(
        entity_name="Product",
        properties=[
            PropertyConfig(name="id", type="number"),
            PropertyConfig(name="name", type="string"),
            PropertyConfig(name="price", type="number"),
            PropertyConfig(name="stock", type="number"),
            PropertyConfig(name="description", type="string", optional=True),
            PropertyConfig(name="isActive", type="boolean")
        ],
        include_cache=False,
        include_validation=False,
        architecture='mvvm'
    )
    
    generator = CodeGenerator(config)
    files = generator.generate_all()
    
    output_dir = Path("./examples/product_mvvm")
    _save_files(files, output_dir)
    
    print(f"✅ {len(files)} arquivos gerados em {output_dir}\n")


def example_blog_post():
    """Exemplo: Entidade BlogPost com Clean Architecture"""
    print("📝 Exemplo 3: BlogPost (Clean Architecture)")
    
    config = GeneratorConfig(
        entity_name="BlogPost",
        properties=[
            PropertyConfig(name="id", type="number"),
            PropertyConfig(
                name="title",
                type="string",
                validation=[
                    ValidationRule(ValidationType.REQUIRED),
                    ValidationRule(ValidationType.MIN_LENGTH, value=5),
                    ValidationRule(ValidationType.MAX_LENGTH, value=200)
                ]
            ),
            PropertyConfig(name="content", type="string"),
            PropertyConfig(name="author", type="string"),
            PropertyConfig(name="published", type="boolean"),
            PropertyConfig(name="publishedAt", type="Date", optional=True),
            PropertyConfig(name="createdAt", type="Date"),
            PropertyConfig(name="updatedAt", type="Date")
        ],
        include_cache=True,
        include_validation=True,
        architecture='clean'
    )
    
    generator = CodeGenerator(config)
    files = generator.generate_all()
    
    output_dir = Path("./examples/blogpost_clean")
    _save_files(files, output_dir)
    
    print(f"✅ {len(files)} arquivos gerados em {output_dir}\n")


def example_minimal():
    """Exemplo: Entidade mínima"""
    print("📝 Exemplo 4: Entidade Mínima")
    
    config = GeneratorConfig(
        entity_name="Category",
        properties=[
            PropertyConfig(name="id", type="number"),
            PropertyConfig(name="name", type="string")
        ],
        architecture='mvvm'
    )
    
    generator = CodeGenerator(config)
    files = generator.generate_all()
    
    output_dir = Path("./examples/category_minimal")
    _save_files(files, output_dir)
    
    print(f"✅ {len(files)} arquivos gerados em {output_dir}\n")


def _save_files(files: dict, output_dir: Path):
    """Salva arquivos no diretório especificado"""
    for file_path, content in files.items():
        full_path = output_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding='utf-8')


def list_generated_files():
    """Lista todos os arquivos gerados nos exemplos"""
    print("\n" + "="*60)
    print("📂 Estrutura de arquivos gerados:")
    print("="*60 + "\n")
    
    examples_dir = Path("./examples")
    if examples_dir.exists():
        for example_dir in sorted(examples_dir.iterdir()):
            if example_dir.is_dir():
                print(f"\n📁 {example_dir.name}/")
                for file in sorted(example_dir.rglob("*.ets")):
                    rel_path = file.relative_to(example_dir)
                    print(f"  ├─ {rel_path}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Exemplos de Geração de Código ArkTS")
    print("="*60 + "\n")
    
    example_clean_architecture_with_validation()
    example_mvvm_simple()
    example_blog_post()
    example_minimal()
    
    list_generated_files()
    
    print("\n" + "="*60)
    print("✨ Todos os exemplos foram gerados com sucesso!")
    print("="*60 + "\n")
