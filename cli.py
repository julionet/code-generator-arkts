# generator/cli.py

import argparse
import sys
from pathlib import Path
from typing import List
from code_generator import (
    CodeGenerator,
    GeneratorConfig,
    PropertyConfig,
    ValidationRule,
    ValidationType
)


class GeneratorCLI:
    """Interface de linha de comando para o gerador de código ArkTS"""
    
    @staticmethod
    def run():
        """Executa o CLI"""
        parser = argparse.ArgumentParser(
            description='🚀 ArkTS Code Generator - Clean Architecture & MVVM',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog='''
Exemplos de uso:
  # Clean Architecture com cache e validações
  python -m generator.cli generate User --props "name:string,email:string,age:number" --cache --validation
  
  # MVVM Tradicional
  python -m generator.cli generate Product --arch mvvm --props "name:string,price:number"
  
  # Propriedades opcionais (adicione ? no final do tipo)
  python -m generator.cli g User --props "name:string,bio:string?"
  
  # Modo interativo
  python -m generator.cli interactive
            '''
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')
        
        # Comando generate
        gen_parser = subparsers.add_parser('generate', aliases=['g'], help='Gera código ArkTS')
        gen_parser.add_argument('entity', help='Nome da entidade (ex: User, Product)')
        gen_parser.add_argument('--props', required=True, help='Propriedades (formato: name:string,email:string)')
        gen_parser.add_argument('--arch', choices=['mvvm', 'clean'], default='clean', help='Arquitetura (padrão: clean)')
        gen_parser.add_argument('--cache', action='store_true', help='Incluir cache local')
        gen_parser.add_argument('--validation', action='store_true', help='Incluir validações')
        gen_parser.add_argument('--output', default='./generated', help='Diretório de saída (padrão: ./generated)')
        
        # Comando interactive
        subparsers.add_parser('interactive', aliases=['i'], help='Modo interativo')
        
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return
        
        if args.command in ['generate', 'g']:
            GeneratorCLI._generate_from_args(args)
        elif args.command in ['interactive', 'i']:
            GeneratorCLI._interactive_mode()
    
    @staticmethod
    def _generate_from_args(args):
        """Gera código ArkTS a partir dos argumentos"""
        try:
            config = GeneratorCLI._parse_config(args)
            
            print(f"\n🎯 Gerando código ArkTS para: {config.entity_name}")
            print(f"📐 Arquitetura: {config.architecture.upper()}")
            print(f"💾 Cache: {'Sim' if config.include_cache else 'Não'}")
            print(f"✅ Validação: {'Sim' if config.include_validation else 'Não'}")
            print(f"📝 Propriedades: {len(config.properties)}")
            
            generator = CodeGenerator(config)
            files = generator.generate_all()
            
            GeneratorCLI._write_files(files, args.output)
            
            print(f"\n✅ {len(files)} arquivos gerados com sucesso!")
            print(f"📁 Localização: {Path(args.output).absolute()}\n")
            
            # Lista arquivos gerados
            print("📄 Arquivos criados:")
            for path in sorted(files.keys()):
                print(f"  ✓ {path}")
            
            print(f"\n💡 Próximos passos:")
            print(f"  1. Revise os arquivos gerados em: {args.output}")
            print(f"  2. Ajuste o BaseURL nas datasources")
            print(f"  3. Configure o AppContainer para injeção de dependências")
            print(f"  4. Implemente a BaseViewModel se necessário\n")
            
        except Exception as e:
            print(f"\n❌ Erro ao gerar código: {str(e)}\n", file=sys.stderr)
            sys.exit(1)
    
    @staticmethod
    def _parse_config(args) -> GeneratorConfig:
        """Converte argumentos em configuração"""
        properties = GeneratorCLI._parse_properties(args.props)
        
        # Adiciona ID automaticamente se não existir
        if not any(p.name == 'id' for p in properties):
            properties.insert(0, PropertyConfig(
                name='id',
                type='number',
                optional=False
            ))
        
        return GeneratorConfig(
            entity_name=args.entity,
            properties=properties,
            include_cache=args.cache,
            include_validation=args.validation,
            architecture=args.arch
        )
    
    @staticmethod
    def _parse_properties(props_string: str) -> List[PropertyConfig]:
        """Parse string de propriedades para ArkTS"""
        properties = []
        
        for prop in props_string.split(','):
            prop = prop.strip()
            if ':' not in prop:
                print(f"⚠️  Propriedade inválida ignorada: {prop}")
                continue
            
            name, type_str = prop.split(':', 1)
            name = name.strip()
            type_str = type_str.strip()
            
            # Verifica se é opcional
            optional = False
            if type_str.endswith('?'):
                optional = True
                type_str = type_str[:-1].strip()
            
            # Valida tipo ArkTS
            valid_types = ['string', 'number', 'boolean', 'Date']
            if type_str not in valid_types:
                print(f"⚠️  Tipo inválido '{type_str}' para propriedade '{name}'. Use: {', '.join(valid_types)}")
                continue
            
            properties.append(PropertyConfig(
                name=name,
                type=type_str,
                optional=optional
            ))
        
        return properties
    
    @staticmethod
    def _write_files(files: dict, output_dir: str):
        """Escreve arquivos ArkTS no sistema"""
        base_path = Path(output_dir)
        
        for file_path, content in files.items():
            full_path = base_path / file_path
            
            # Cria diretórios
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Escreve arquivo
            full_path.write_text(content, encoding='utf-8')
    
    @staticmethod
    def _interactive_mode():
        """Modo interativo para geração de código"""
        print("\n" + "="*60)
        print("🎯 Modo Interativo - Gerador de Código ArkTS")
        print("="*60 + "\n")
        
        try:
            # Nome da entidade
            entity_name = input("📝 Nome da entidade (ex: User, Product): ").strip()
            if not entity_name:
                print("❌ Nome da entidade é obrigatório!")
                return
            
            # Capitaliza primeira letra
            entity_name = entity_name[0].upper() + entity_name[1:]
            
            # Arquitetura
            print("\n📐 Escolha a arquitetura:")
            print("  1. Clean Architecture (recomendado)")
            print("  2. MVVM Tradicional")
            arch_choice = input("Escolha (1-2) [1]: ").strip() or '1'
            architecture = 'clean' if arch_choice == '1' else 'mvvm'
            
            # Propriedades
            print("\n📋 Defina as propriedades:")
            print("  Formato: nome:tipo")
            print("  Tipos disponíveis: string, number, boolean, Date")
            print("  Adicione '?' para opcional: nome:string?")
            print("  Digite 'fim' para finalizar\n")
            
            properties = [PropertyConfig(name='id', type='number', optional=False)]
            
            prop_count = 1
            while True:
                prop_input = input(f"  Propriedade {prop_count} (ou 'fim'): ").strip()
                
                if prop_input.lower() == 'fim':
                    break
                
                if not prop_input:
                    continue
                
                if ':' not in prop_input:
                    print("  ⚠️  Formato inválido! Use: nome:tipo")
                    continue
                
                name, type_str = prop_input.split(':', 1)
                name = name.strip()
                type_str = type_str.strip()
                
                optional = False
                if type_str.endswith('?'):
                    optional = True
                    type_str = type_str[:-1].strip()
                
                valid_types = ['string', 'number', 'boolean', 'Date']
                if type_str not in valid_types:
                    print(f"  ⚠️  Tipo inválido! Use: {', '.join(valid_types)}")
                    continue
                
                properties.append(PropertyConfig(
                    name=name,
                    type=type_str,
                    optional=optional
                ))
                
                print(f"  ✓ Adicionado: {name}: {type_str}{'?' if optional else ''}")
                prop_count += 1
            
            if len(properties) == 1:  # Apenas ID
                print("\n⚠️  Nenhuma propriedade adicionada! Abortando...")
                return
            
            # Opções
            print("\n⚙️  Opções adicionais:")
            include_cache = input("  💾 Incluir cache local? (s/N): ").strip().lower() == 's'
            include_validation = input("  ✅ Incluir validações? (s/N): ").strip().lower() == 's'
            output_dir = input("  📁 Diretório de saída [./generated]: ").strip() or './generated'
            
            # Resumo
            print("\n" + "="*60)
            print("📊 Resumo da configuração:")
            print("="*60)
            print(f"  Entidade: {entity_name}")
            print(f"  Arquitetura: {architecture.upper()}")
            print(f"  Propriedades: {len(properties)}")
            for prop in properties:
                opt_marker = '?' if prop.optional else ''
                print(f"    - {prop.name}: {prop.type}{opt_marker}")
            print(f"  Cache: {'Sim' if include_cache else 'Não'}")
            print(f"  Validação: {'Sim' if include_validation else 'Não'}")
            print(f"  Output: {output_dir}")
            print("="*60)
            
            confirm = input("\n✨ Gerar código? (S/n): ").strip().lower()
            if confirm == 'n':
                print("❌ Operação cancelada.")
                return
            
            # Gera código
            config = GeneratorConfig(
                entity_name=entity_name,
                properties=properties,
                include_cache=include_cache,
                include_validation=include_validation,
                architecture=architecture
            )
            
            generator = CodeGenerator(config)
            files = generator.generate_all()
            
            GeneratorCLI._write_files(files, output_dir)
            
            print(f"\n✅ {len(files)} arquivos ArkTS gerados com sucesso!")
            print(f"📁 Localização: {Path(output_dir).absolute()}\n")
            
            # Lista alguns arquivos
            print("📄 Alguns arquivos criados:")
            for path in list(sorted(files.keys()))[:10]:
                print(f"  ✓ {path}")
            if len(files) > 10:
                print(f"  ... e mais {len(files) - 10} arquivos")
            
            print("\n🎉 Geração concluída!\n")
            
        except KeyboardInterrupt:
            print("\n\n❌ Operação cancelada pelo usuário.\n")
        except Exception as e:
            print(f"\n❌ Erro: {str(e)}\n", file=sys.stderr)


if __name__ == "__main__":
    GeneratorCLI.run()
