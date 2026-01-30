# generator/code_generator.py

from typing import List, Dict, Optional, Literal
from dataclasses import dataclass, field
from enum import Enum


class ValidationType(Enum):
    """Tipos de validação suportados"""
    REQUIRED = "required"
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    EMAIL = "email"
    MIN = "min"
    MAX = "max"
    PATTERN = "pattern"


@dataclass
class ValidationRule:
    """Regra de validação para propriedades"""
    type: ValidationType
    value: Optional[any] = None
    message: Optional[str] = None


@dataclass
class PropertyConfig:
    """Configuração de propriedade da entidade"""
    name: str
    type: str  # Ex: "string", "number", "boolean", "Date"
    optional: bool = False
    validation: List[ValidationRule] = field(default_factory=list)


@dataclass
class GeneratorConfig:
    """Configuração principal do gerador"""
    entity_name: str
    properties: List[PropertyConfig]
    include_cache: bool = False
    include_validation: bool = False
    architecture: Literal['mvvm', 'clean'] = 'clean'


class CodeGenerator:
    """Gerador de código ArkTS para arquiteturas Clean Architecture e MVVM"""
    
    def __init__(self, config: GeneratorConfig):
        self.config = config
        self.entity_name_lower = config.entity_name.lower()
        self.entity_name_plural = self._pluralize(self.entity_name_lower)
    
    def generate_all(self) -> Dict[str, str]:
        """Gera todos os arquivos ArkTS baseado na arquitetura escolhida"""
        files = {}
        
        if self.config.architecture == 'clean':
            # Clean Architecture
            files[f"domain/entities/{self.config.entity_name}.ets"] = self._generate_entity()
            files[f"domain/repositories/I{self.config.entity_name}Repository.ets"] = self._generate_repository_interface()
            files[f"domain/usecases/{self.entity_name_lower}/Get{self.entity_name_plural}UseCase.ets"] = self._generate_get_all_usecase()
            files[f"domain/usecases/{self.entity_name_lower}/Get{self.config.entity_name}ByIdUseCase.ets"] = self._generate_get_by_id_usecase()
            files[f"domain/usecases/{self.entity_name_lower}/Create{self.config.entity_name}UseCase.ets"] = self._generate_create_usecase()
            files[f"domain/usecases/{self.entity_name_lower}/Update{self.config.entity_name}UseCase.ets"] = self._generate_update_usecase()
            files[f"domain/usecases/{self.entity_name_lower}/Delete{self.config.entity_name}UseCase.ets"] = self._generate_delete_usecase()
            
            files[f"data/models/{self.config.entity_name}Model.ets"] = self._generate_model()
            files[f"data/datasources/I{self.config.entity_name}RemoteDataSource.ets"] = self._generate_remote_datasource_interface()
            files[f"data/datasources/{self.config.entity_name}RemoteDataSourceImpl.ets"] = self._generate_remote_datasource_impl()
            
            if self.config.include_cache:
                files[f"data/datasources/I{self.config.entity_name}LocalDataSource.ets"] = self._generate_local_datasource_interface()
                files[f"data/datasources/{self.config.entity_name}LocalDataSourceImpl.ets"] = self._generate_local_datasource_impl()
            
            files[f"data/repositories/{self.config.entity_name}RepositoryImpl.ets"] = self._generate_repository_impl()
            files[f"presentation/viewmodels/{self.config.entity_name}ViewModel.ets"] = self._generate_viewmodel()
            files[f"presentation/views/pages/{self.config.entity_name}Page.ets"] = self._generate_page()
            
        else:
            # MVVM Tradicional
            files[f"data/models/{self.config.entity_name}.ets"] = self._generate_simple_model()
            files[f"data/repositories/{self.config.entity_name}Repository.ets"] = self._generate_simple_repository()
            files[f"viewmodels/{self.config.entity_name}ViewModel.ets"] = self._generate_simple_viewmodel()
            files[f"views/pages/{self.config.entity_name}Page.ets"] = self._generate_simple_page()
        
        return files
    
    def _pluralize(self, word: str) -> str:
        """Pluraliza uma palavra em inglês"""
        if word.endswith('y'):
            return word[:-1] + 'ies'
        if word.endswith(('s', 'x', 'z')):
            return word + 'es'
        return word + 's'
    
    # ==========================================
    # CLEAN ARCHITECTURE GENERATORS
    # ==========================================
    
    def _generate_entity(self) -> str:
        """Gera a entidade de domínio em ArkTS"""
        properties = self._generate_properties()
        constructor_params = self._generate_constructor_params()
        validations = self._generate_validations() if self.config.include_validation else ""
        copy_method = self._generate_copy_method()
        to_json_method = self._generate_to_json_method()
        from_json_method = self._generate_from_json_method()
        
        validation_call = "this.validate();" if self.config.include_validation else ""
        validation_method = f"\n  {validations}\n  " if self.config.include_validation else ""
        
        return f'''// domain/entities/{self.config.entity_name}.ets

export class {self.config.entity_name} {{
{properties}
  
  constructor(
{constructor_params}
  ) {{
    {validation_call}
  }}
  {validation_method}
{self._indent_code(copy_method, 1)}
  
{self._indent_code(to_json_method, 1)}
  
{self._indent_code(from_json_method, 1)}
}}'''
    
    def _generate_properties(self) -> str:
        """Gera as propriedades da classe"""
        lines = []
        for prop in self.config.properties:
            optional = '?' if prop.optional else ''
            readonly = 'readonly ' if prop.name == 'id' else ''
            lines.append(f"  public {readonly}{prop.name}{optional}: {prop.type};")
        return "\n".join(lines)
    
    def _generate_constructor_params(self) -> str:
        """Gera os parâmetros do construtor"""
        params = []
        for prop in self.config.properties:
            optional = '?' if prop.optional else ''
            default_value = self._get_default_value(prop)
            params.append(f"    public {prop.name}{optional}: {prop.type}{default_value}")
        return ",\n".join(params)
    
    def _generate_validations(self) -> str:
        """Gera o método de validação"""
        if not self.config.include_validation:
            return ""
        
        validation_code = "private validate(): void {\n"
        
        for prop in self.config.properties:
            if not prop.validation:
                continue
            
            for rule in prop.validation:
                if rule.type == ValidationType.REQUIRED:
                    if prop.type == 'string':
                        validation_code += f"    if (!this.{prop.name} || this.{prop.name}.trim().length === 0) {{\n"
                        validation_code += f"      throw new Error('{rule.message or prop.name + ' é obrigatório'}');\n"
                        validation_code += "    }\n"
                    else:
                        validation_code += f"    if (this.{prop.name} === undefined || this.{prop.name} === null) {{\n"
                        validation_code += f"      throw new Error('{rule.message or prop.name + ' é obrigatório'}');\n"
                        validation_code += "    }\n"
                
                elif rule.type == ValidationType.MIN_LENGTH:
                    validation_code += f"    if (this.{prop.name}.length < {rule.value}) {{\n"
                    validation_code += f"      throw new Error('{rule.message or prop.name + ' deve ter no mínimo ' + str(rule.value) + ' caracteres'}');\n"
                    validation_code += "    }\n"
                
                elif rule.type == ValidationType.MAX_LENGTH:
                    validation_code += f"    if (this.{prop.name}.length > {rule.value}) {{\n"
                    validation_code += f"      throw new Error('{rule.message or prop.name + ' deve ter no máximo ' + str(rule.value) + ' caracteres'}');\n"
                    validation_code += "    }\n"
                
                elif rule.type == ValidationType.EMAIL:
                    validation_code += f"    const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;\n"
                    validation_code += f"    if (!emailRegex.test(this.{prop.name})) {{\n"
                    validation_code += f"      throw new Error('{rule.message or prop.name + ' inválido'}');\n"
                    validation_code += "    }\n"
                
                elif rule.type == ValidationType.MIN:
                    validation_code += f"    if (this.{prop.name} < {rule.value}) {{\n"
                    validation_code += f"      throw new Error('{rule.message or prop.name + ' deve ser maior ou igual a ' + str(rule.value)}');\n"
                    validation_code += "    }\n"
                
                elif rule.type == ValidationType.MAX:
                    validation_code += f"    if (this.{prop.name} > {rule.value}) {{\n"
                    validation_code += f"      throw new Error('{rule.message or prop.name + ' deve ser menor ou igual a ' + str(rule.value)}');\n"
                    validation_code += "    }\n"
                
                elif rule.type == ValidationType.PATTERN:
                    validation_code += f"    const pattern = new RegExp('{rule.value}');\n"
                    validation_code += f"    if (!pattern.test(this.{prop.name})) {{\n"
                    validation_code += f"      throw new Error('{rule.message or prop.name + ' inválido'}');\n"
                    validation_code += "    }\n"
        
        validation_code += "  }"
        return validation_code
    
    def _generate_copy_method(self) -> str:
        """Gera o método copy"""
        updates_params = ", ".join([f"{p.name}?: {p.type}" for p in self.config.properties])
        copy_args = ",\n      ".join([f"updates.{p.name} ?? this.{p.name}" for p in self.config.properties])
        
        return f'''/**
   * Cria uma cópia do objeto
   */
  copy(updates?: {{ {updates_params} }}): {self.config.entity_name} {{
    if (!updates) updates = {{}};
    return new {self.config.entity_name}(
      {copy_args}
    );
  }}'''
    
    def _generate_to_json_method(self) -> str:
        """Gera o método toJson"""
        json_fields = []
        for prop in self.config.properties:
            if prop.type == 'Date':
                if prop.optional:
                    json_fields.append(f"{prop.name}: this.{prop.name}?.toISOString()")
                else:
                    json_fields.append(f"{prop.name}: this.{prop.name}.toISOString()")
            else:
                json_fields.append(f"{prop.name}: this.{prop.name}")
        
        json_body = ",\n      ".join(json_fields)
        
        return f'''/**
   * Converte para objeto simples
   */
  toJson(): Record<string, Object> {{
    return {{
      {json_body}
    }};
  }}'''
    
    def _generate_from_json_method(self) -> str:
        """Gera o método fromJson estático"""
        from_json_args = []
        for prop in self.config.properties:
            if prop.type == 'Date':
                from_json_args.append(f"new Date(json.{prop.name} as string)")
            else:
                from_json_args.append(f"json.{prop.name} as {prop.type}")
        
        from_json_body = ",\n      ".join(from_json_args)
        
        return f'''/**
   * Cria instância a partir de JSON
   */
  static fromJson(json: Record<string, Object>): {self.config.entity_name} {{
    return new {self.config.entity_name}(
      {from_json_body}
    );
  }}'''
    
    def _generate_repository_interface(self) -> str:
        """Gera a interface do repositório"""
        return f'''// domain/repositories/I{self.config.entity_name}Repository.ets

import {{ {self.config.entity_name} }} from '../entities/{self.config.entity_name}';

export interface I{self.config.entity_name}Repository {{
  get{self.entity_name_plural}(): Promise<{self.config.entity_name}[]>;
  get{self.config.entity_name}ById(id: number): Promise<{self.config.entity_name}>;
  create{self.config.entity_name}(entity: {self.config.entity_name}): Promise<{self.config.entity_name}>;
  update{self.config.entity_name}(entity: {self.config.entity_name}): Promise<{self.config.entity_name}>;
  delete{self.config.entity_name}(id: number): Promise<void>;
}}'''
    
    def _generate_get_all_usecase(self) -> str:
        """Gera o use case GetAll"""
        return f'''// domain/usecases/{self.entity_name_lower}/Get{self.entity_name_plural}UseCase.ets

import {{ {self.config.entity_name} }} from '../../entities/{self.config.entity_name}';
import {{ I{self.config.entity_name}Repository }} from '../../repositories/I{self.config.entity_name}Repository';

export class Get{self.entity_name_plural}UseCase {{
  constructor(private repository: I{self.config.entity_name}Repository) {{}}
  
  async execute(): Promise<{self.config.entity_name}[]> {{
    return await this.repository.get{self.entity_name_plural}();
  }}
}}'''
    
    def _generate_get_by_id_usecase(self) -> str:
        """Gera o use case GetById"""
        return f'''// domain/usecases/{self.entity_name_lower}/Get{self.config.entity_name}ByIdUseCase.ets

import {{ {self.config.entity_name} }} from '../../entities/{self.config.entity_name}';
import {{ I{self.config.entity_name}Repository }} from '../../repositories/I{self.config.entity_name}Repository';

export class Get{self.config.entity_name}ByIdUseCase {{
  constructor(private repository: I{self.config.entity_name}Repository) {{}}
  
  async execute(id: number): Promise<{self.config.entity_name}> {{
    if (id <= 0) {{
      throw new Error('ID inválido');
    }}
    return await this.repository.get{self.config.entity_name}ById(id);
  }}
}}'''
    
    def _generate_create_usecase(self) -> str:
        """Gera o use case Create"""
        params = self._get_create_params()
        entity_creation = self._get_entity_creation()
        
        return f'''// domain/usecases/{self.entity_name_lower}/Create{self.config.entity_name}UseCase.ets

import {{ {self.config.entity_name} }} from '../../entities/{self.config.entity_name}';
import {{ I{self.config.entity_name}Repository }} from '../../repositories/I{self.config.entity_name}Repository';

export class Create{self.config.entity_name}UseCase {{
  constructor(private repository: I{self.config.entity_name}Repository) {{}}
  
  async execute({params}): Promise<{self.config.entity_name}> {{
    const entity = new {self.config.entity_name}({entity_creation});
    return await this.repository.create{self.config.entity_name}(entity);
  }}
}}'''
    
    def _generate_update_usecase(self) -> str:
        """Gera o use case Update"""
        return f'''// domain/usecases/{self.entity_name_lower}/Update{self.config.entity_name}UseCase.ets

import {{ {self.config.entity_name} }} from '../../entities/{self.config.entity_name}';
import {{ I{self.config.entity_name}Repository }} from '../../repositories/I{self.config.entity_name}Repository';

export class Update{self.config.entity_name}UseCase {{
  constructor(private repository: I{self.config.entity_name}Repository) {{}}
  
  async execute(id: number, updates: Partial<{self.config.entity_name}>): Promise<{self.config.entity_name}> {{
    const existing = await this.repository.get{self.config.entity_name}ById(id);
    const updated = existing.copy(updates);
    return await this.repository.update{self.config.entity_name}(updated);
  }}
}}'''
    
    def _generate_delete_usecase(self) -> str:
        """Gera o use case Delete"""
        return f'''// domain/usecases/{self.entity_name_lower}/Delete{self.config.entity_name}UseCase.ets

import {{ I{self.config.entity_name}Repository }} from '../../repositories/I{self.config.entity_name}Repository';

export class Delete{self.config.entity_name}UseCase {{
  constructor(private repository: I{self.config.entity_name}Repository) {{}}
  
  async execute(id: number): Promise<void> {{
    if (id <= 0) {{
      throw new Error('ID inválido');
    }}
    await this.repository.delete{self.config.entity_name}(id);
  }}
}}'''
    
    def _generate_model(self) -> str:
        """Gera o modelo DTO e Mapper"""
        dto_properties = self._generate_dto_properties()
        to_domain_mapping = self._generate_to_domain_mapping()
        to_dto_mapping = self._generate_to_dto_mapping()
        
        return f'''// data/models/{self.config.entity_name}Model.ets

import {{ {self.config.entity_name} }} from '../../domain/entities/{self.config.entity_name}';

export interface {self.config.entity_name}DTO {{
{dto_properties}
}}

export class {self.config.entity_name}Mapper {{
  static toDomain(dto: {self.config.entity_name}DTO): {self.config.entity_name} {{
    return new {self.config.entity_name}(
{to_domain_mapping}
    );
  }}
  
  static toDTO(entity: {self.config.entity_name}): {self.config.entity_name}DTO {{
    return {{
{to_dto_mapping}
    }};
  }}
  
  static toDomainList(dtos: {self.config.entity_name}DTO[]): {self.config.entity_name}[] {{
    return dtos.map(dto => this.toDomain(dto));
  }}
  
  static toDTOList(entities: {self.config.entity_name}[]): {self.config.entity_name}DTO[] {{
    return entities.map(entity => this.toDTO(entity));
  }}
}}'''
    
    def _generate_remote_datasource_interface(self) -> str:
        """Gera a interface do datasource remoto"""
        return f'''// data/datasources/I{self.config.entity_name}RemoteDataSource.ets

import {{ {self.config.entity_name}DTO }} from '../models/{self.config.entity_name}Model';

export interface I{self.config.entity_name}RemoteDataSource {{
  fetch{self.entity_name_plural}(): Promise<{self.config.entity_name}DTO[]>;
  fetch{self.config.entity_name}ById(id: number): Promise<{self.config.entity_name}DTO>;
  create{self.config.entity_name}(dto: {self.config.entity_name}DTO): Promise<{self.config.entity_name}DTO>;
  update{self.config.entity_name}(dto: {self.config.entity_name}DTO): Promise<{self.config.entity_name}DTO>;
  delete{self.config.entity_name}(id: number): Promise<void>;
}}'''
    
    def _generate_remote_datasource_impl(self) -> str:
        """Gera a implementação do datasource remoto"""
        return f'''// data/datasources/{self.config.entity_name}RemoteDataSourceImpl.ets

import http from '@ohos.net.http';
import {{ {self.config.entity_name}DTO }} from '../models/{self.config.entity_name}Model';
import {{ I{self.config.entity_name}RemoteDataSource }} from './I{self.config.entity_name}RemoteDataSource';

export class {self.config.entity_name}RemoteDataSourceImpl implements I{self.config.entity_name}RemoteDataSource {{
  private baseUrl: string = 'https://api.example.com';
  private endpoint: string = '/{self.entity_name_lower}s';
  
  async fetch{self.entity_name_plural}(): Promise<{self.config.entity_name}DTO[]> {{
    const response = await this.makeRequest<{{ data: {self.config.entity_name}DTO[] }}>(
      this.endpoint,
      'GET'
    );
    return response.data;
  }}
  
  async fetch{self.config.entity_name}ById(id: number): Promise<{self.config.entity_name}DTO> {{
    const response = await this.makeRequest<{{ data: {self.config.entity_name}DTO }}>(
      `${{this.endpoint}}/${{id}}`,
      'GET'
    );
    return response.data;
  }}
  
  async create{self.config.entity_name}(dto: {self.config.entity_name}DTO): Promise<{self.config.entity_name}DTO> {{
    const response = await this.makeRequest<{{ data: {self.config.entity_name}DTO }}>(
      this.endpoint,
      'POST',
      dto
    );
    return response.data;
  }}
  
  async update{self.config.entity_name}(dto: {self.config.entity_name}DTO): Promise<{self.config.entity_name}DTO> {{
    const response = await this.makeRequest<{{ data: {self.config.entity_name}DTO }}>(
      `${{this.endpoint}}/${{dto.id}}`,
      'PUT',
      dto
    );
    return response.data;
  }}
  
  async delete{self.config.entity_name}(id: number): Promise<void> {{
    await this.makeRequest<void>(`${{this.endpoint}}/${{id}}`, 'DELETE');
  }}
  
  private async makeRequest<T>(
    endpoint: string,
    method: string,
    body?: Object
  ): Promise<T> {{
    return new Promise((resolve, reject) => {{
      const httpRequest = http.createHttp();
      
      httpRequest.request(`${{this.baseUrl}}${{endpoint}}`, {{
        method: method as http.RequestMethod,
        header: {{ 'Content-Type': 'application/json' }},
        extraData: body ? JSON.stringify(body) : undefined,
        connectTimeout: 30000,
        readTimeout: 30000,
      }}, (err, data) => {{
        if (!err && (data.responseCode === 200 || data.responseCode === 201)) {{
          resolve(JSON.parse(data.result as string) as T);
        }} else {{
          reject(new Error(err?.message || 'Request failed'));
        }}
        httpRequest.destroy();
      }});
    }});
  }}
}}'''
    
    def _generate_local_datasource_interface(self) -> str:
        """Gera a interface do datasource local"""
        return f'''// data/datasources/I{self.config.entity_name}LocalDataSource.ets

import {{ {self.config.entity_name}DTO }} from '../models/{self.config.entity_name}Model';

export interface I{self.config.entity_name}LocalDataSource {{
  getCached{self.entity_name_plural}(): Promise<{self.config.entity_name}DTO[]>;
  cache{self.entity_name_plural}(dtos: {self.config.entity_name}DTO[]): Promise<void>;
  clearCache(): Promise<void>;
}}'''
    
    def _generate_local_datasource_impl(self) -> str:
        """Gera a implementação do datasource local"""
        return f'''// data/datasources/{self.config.entity_name}LocalDataSourceImpl.ets

import preferences from '@ohos.data.preferences';
import {{ {self.config.entity_name}DTO }} from '../models/{self.config.entity_name}Model';
import {{ I{self.config.entity_name}LocalDataSource }} from './I{self.config.entity_name}LocalDataSource';

export class {self.config.entity_name}LocalDataSourceImpl implements I{self.config.entity_name}LocalDataSource {{
  private readonly CACHE_KEY = '{self.entity_name_lower}_cache';
  private preferencesStore?: preferences.Preferences;
  
  async initialize(context: Context): Promise<void> {{
    this.preferencesStore = await preferences.getPreferences(context, 'app_cache');
  }}
  
  async getCached{self.entity_name_plural}(): Promise<{self.config.entity_name}DTO[]> {{
    if (!this.preferencesStore) {{
      throw new Error('DataSource not initialized');
    }}
    
    const cached = await this.preferencesStore.get(this.CACHE_KEY, '[]');
    return JSON.parse(cached as string) as {self.config.entity_name}DTO[];
  }}
  
  async cache{self.entity_name_plural}(dtos: {self.config.entity_name}DTO[]): Promise<void> {{
    if (!this.preferencesStore) {{
      throw new Error('DataSource not initialized');
    }}
    
    await this.preferencesStore.put(this.CACHE_KEY, JSON.stringify(dtos));
    await this.preferencesStore.flush();
  }}
  
  async clearCache(): Promise<void> {{
    if (!this.preferencesStore) {{
      throw new Error('DataSource not initialized');
    }}
    
    await this.preferencesStore.delete(this.CACHE_KEY);
    await this.preferencesStore.flush();
  }}
}}'''
    
    def _generate_repository_impl(self) -> str:
        """Gera a implementação do repositório"""
        cache_import = ""
        cache_constructor_param = ""
        cache_constructor_assign = ""
        cache_logic = ""
        
        if self.config.include_cache:
            cache_import = f"import {{ I{self.config.entity_name}LocalDataSource }} from '../datasources/I{self.config.entity_name}LocalDataSource';"
            cache_constructor_param = f",\n    private localDataSource: I{self.config.entity_name}LocalDataSource"
            cache_logic = f'''try {{
      const dtos = await this.remoteDataSource.fetch{self.entity_name_plural}();
      await this.localDataSource.cache{self.entity_name_plural}(dtos);
      return {self.config.entity_name}Mapper.toDomainList(dtos);
    }} catch (error) {{
      const cachedDtos = await this.localDataSource.getCached{self.entity_name_plural}();
      return {self.config.entity_name}Mapper.toDomainList(cachedDtos);
    }}'''
        else:
            cache_logic = f'''const dtos = await this.remoteDataSource.fetch{self.entity_name_plural}();
    return {self.config.entity_name}Mapper.toDomainList(dtos);'''
        
        return f'''// data/repositories/{self.config.entity_name}RepositoryImpl.ets

import {{ {self.config.entity_name} }} from '../../domain/entities/{self.config.entity_name}';
import {{ I{self.config.entity_name}Repository }} from '../../domain/repositories/I{self.config.entity_name}Repository';
import {{ {self.config.entity_name}Mapper }} from '../models/{self.config.entity_name}Model';
import {{ I{self.config.entity_name}RemoteDataSource }} from '../datasources/I{self.config.entity_name}RemoteDataSource';
{cache_import}

export class {self.config.entity_name}RepositoryImpl implements I{self.config.entity_name}Repository {{
  constructor(
    private remoteDataSource: I{self.config.entity_name}RemoteDataSource{cache_constructor_param}
  ) {{}}
  
  async get{self.entity_name_plural}(): Promise<{self.config.entity_name}[]> {{
    {cache_logic}
  }}
  
  async get{self.config.entity_name}ById(id: number): Promise<{self.config.entity_name}> {{
    const dto = await this.remoteDataSource.fetch{self.config.entity_name}ById(id);
    return {self.config.entity_name}Mapper.toDomain(dto);
  }}
  
  async create{self.config.entity_name}(entity: {self.config.entity_name}): Promise<{self.config.entity_name}> {{
    const dto = {self.config.entity_name}Mapper.toDTO(entity);
    const createdDto = await this.remoteDataSource.create{self.config.entity_name}(dto);
    return {self.config.entity_name}Mapper.toDomain(createdDto);
  }}
  
  async update{self.config.entity_name}(entity: {self.config.entity_name}): Promise<{self.config.entity_name}> {{
    const dto = {self.config.entity_name}Mapper.toDTO(entity);
    const updatedDto = await this.remoteDataSource.update{self.config.entity_name}(dto);
    return {self.config.entity_name}Mapper.toDomain(updatedDto);
  }}
  
  async delete{self.config.entity_name}(id: number): Promise<void> {{
    await this.remoteDataSource.delete{self.config.entity_name}(id);
  }}
}}'''
    
    def _generate_viewmodel(self) -> str:
        """Gera o ViewModel"""
        return f'''// presentation/viewmodels/{self.config.entity_name}ViewModel.ets

import {{ BaseViewModel }} from './base/BaseViewModel';
import {{ {self.config.entity_name} }} from '../../domain/entities/{self.config.entity_name}';
import {{ Get{self.entity_name_plural}UseCase }} from '../../domain/usecases/{self.entity_name_lower}/Get{self.entity_name_plural}UseCase';
import {{ Get{self.config.entity_name}ByIdUseCase }} from '../../domain/usecases/{self.entity_name_lower}/Get{self.config.entity_name}ByIdUseCase';
import {{ Create{self.config.entity_name}UseCase }} from '../../domain/usecases/{self.entity_name_lower}/Create{self.config.entity_name}UseCase';
import {{ Update{self.config.entity_name}UseCase }} from '../../domain/usecases/{self.entity_name_lower}/Update{self.config.entity_name}UseCase';
import {{ Delete{self.config.entity_name}UseCase }} from '../../domain/usecases/{self.entity_name_lower}/Delete{self.config.entity_name}UseCase';

@Observed
export class {self.config.entity_name}ViewModel extends BaseViewModel {{
  @State {self.entity_name_lower}s: {self.config.entity_name}[] = [];
  @State selected{self.config.entity_name}: {self.config.entity_name} | null = null;
  
  constructor(
    private get{self.entity_name_plural}UseCase: Get{self.entity_name_plural}UseCase,
    private get{self.config.entity_name}ByIdUseCase: Get{self.config.entity_name}ByIdUseCase,
    private create{self.config.entity_name}UseCase: Create{self.config.entity_name}UseCase,
    private update{self.config.entity_name}UseCase: Update{self.config.entity_name}UseCase,
    private delete{self.config.entity_name}UseCase: Delete{self.config.entity_name}UseCase
  ) {{
    super();
  }}
  
  async load{self.entity_name_plural}(): Promise<void> {{
    await this.executeUseCase(
      () => this.get{self.entity_name_plural}UseCase.execute(),
      (result) => {{
        this.{self.entity_name_lower}s = result;
      }}
    );
  }}
  
  async load{self.config.entity_name}ById(id: number): Promise<void> {{
    await this.executeUseCase(
      () => this.get{self.config.entity_name}ByIdUseCase.execute(id),
      (result) => {{
        this.selected{self.config.entity_name} = result;
      }}
    );
  }}
  
  async create{self.config.entity_name}({self._get_create_params()}): Promise<boolean> {{
    let success = false;
    await this.executeUseCase(
      () => this.create{self.config.entity_name}UseCase.execute({self._get_create_args()}),
      (result) => {{
        this.{self.entity_name_lower}s.push(result);
        success = true;
      }}
    );
    return success;
  }}
  
  async update{self.config.entity_name}(id: number, updates: Partial<{self.config.entity_name}>): Promise<boolean> {{
    let success = false;
    await this.executeUseCase(
      () => this.update{self.config.entity_name}UseCase.execute(id, updates),
      (result) => {{
        const index = this.{self.entity_name_lower}s.findIndex(e => e.id === id);
        if (index !== -1) {{
          this.{self.entity_name_lower}s[index] = result;
        }}
        success = true;
      }}
    );
    return success;
  }}
  
  async delete{self.config.entity_name}(id: number): Promise<boolean> {{
    let success = false;
    await this.executeUseCase(
      () => this.delete{self.config.entity_name}UseCase.execute(id),
      () => {{
        this.{self.entity_name_lower}s = this.{self.entity_name_lower}s.filter(e => e.id !== id);
        success = true;
      }}
    );
    return success;
  }}
  
  select{self.config.entity_name}(entity: {self.config.entity_name}): void {{
    this.selected{self.config.entity_name} = entity;
  }}
  
  clearSelected(): void {{
    this.selected{self.config.entity_name} = null;
  }}
  
  onDestroy(): void {{
    this.{self.entity_name_lower}s = [];
    this.selected{self.config.entity_name} = null;
  }}
}}'''
    
    def _generate_page(self) -> str:
        """Gera a página/view"""
        first_prop = next((p for p in self.config.properties if p.type == 'string' and p.name != 'id'), None)
        second_prop = next((p for p in self.config.properties if p.type == 'string' and p.name != 'id' and p.name != (first_prop.name if first_prop else '')), None)
        
        first_display = first_prop.name if first_prop else 'name'
        second_display_code = f'''
        Text(entity.{second_prop.name})
          .fontSize(14)
          .fontColor($r('app.color.text_secondary'))''' if second_prop else ''
        
        return f'''// presentation/views/pages/{self.config.entity_name}Page.ets

import {{ {self.config.entity_name}ViewModel }} from '../../viewmodels/{self.config.entity_name}ViewModel';
import {{ {self.config.entity_name} }} from '../../../domain/entities/{self.config.entity_name}';
import {{ AppContainer }} from '../../../di/AppContainer';
import promptAction from '@ohos.promptAction';

@Entry
@Component
struct {self.config.entity_name}Page {{
  private container: AppContainer = AppContainer.getInstance();
  @State private viewModel: {self.config.entity_name}ViewModel = this.container.create{self.config.entity_name}ViewModel();
  
  aboutToAppear() {{
    this.viewModel.load{self.entity_name_plural}();
  }}
  
  aboutToDisappear() {{
    this.viewModel.onDestroy();
  }}
  
  @Builder
  {self.config.entity_name}ListItem(entity: {self.config.entity_name}) {{
    Row() {{
      Column({{ space: 4 }}) {{
        Text(entity.{first_display})
          .fontSize(16)
          .fontWeight(FontWeight.Medium)
          .fontColor($r('app.color.text_primary')){second_display_code}
      }}
      .alignItems(HorizontalAlign.Start)
      .layoutWeight(1)
      
      Button('Deletar')
        .fontSize(14)
        .onClick(async () => {{
          const success = await this.viewModel.delete{self.config.entity_name}(entity.id);
          if (success) {{
            promptAction.showToast({{ message: 'Deletado com sucesso', duration: 2000 }});
          }}
        }})
    }}
    .width('100%')
    .padding(16)
    .backgroundColor(Color.White)
    .borderRadius(8)
    .onClick(() => {{
      this.viewModel.select{self.config.entity_name}(entity);
    }})
  }}
  
  @Builder
  EmptyState() {{
    Column({{ space: 16 }}) {{
      Text('Nenhum registro encontrado')
        .fontSize(16)
        .fontColor($r('app.color.text_secondary'))
      
      Button('Recarregar')
        .onClick(() => {{
          this.viewModel.load{self.entity_name_plural}();
        }})
    }}
    .width('100%')
    .height('100%')
    .justifyContent(FlexAlign.Center)
  }}
  
  build() {{
    Navigation() {{
      Column() {{
        if (this.viewModel.isLoading && this.viewModel.{self.entity_name_lower}s.length === 0) {{
          LoadingProgress()
            .width(60)
            .height(60)
        }} else if (this.viewModel.errorMessage) {{
          Text(this.viewModel.errorMessage)
            .fontSize(16)
            .fontColor(Color.Red)
            .padding(16)
        }} else if (this.viewModel.{self.entity_name_lower}s.length === 0) {{
          this.EmptyState();
        }} else {{
          List({{ space: 8 }}) {{
            ForEach(
              this.viewModel.{self.entity_name_lower}s,
              (entity: {self.config.entity_name}) => {{
                ListItem() {{
                  this.{self.config.entity_name}ListItem(entity);
                }}
              }},
              (entity: {self.config.entity_name}) => entity.id.toString()
            )
          }}
          .width('100%')
          .layoutWeight(1)
          .padding(16)
        }}
      }}
      .width('100%')
      .height('100%')
    }}
    .title('{self.config.entity_name}s')
    .titleMode(NavigationTitleMode.Mini)
  }}
}}'''
    
    # ==========================================
    # MVVM TRADICIONAL GENERATORS
    # ==========================================
    
    def _generate_simple_model(self) -> str:
        """Gera modelo simples para MVVM"""
        return self._generate_entity()
    
    def _generate_simple_repository(self) -> str:
        """Gera repositório simples para MVVM"""
        return f'''// data/repositories/{self.config.entity_name}Repository.ets

import {{ {self.config.entity_name} }} from '../models/{self.config.entity_name}';
import {{ ApiService }} from '../datasources/remote/ApiService';

export class {self.config.entity_name}Repository {{
  private apiService: ApiService = new ApiService();
  private endpoint: string = '/{self.entity_name_lower}s';
  
  async get{self.entity_name_plural}(): Promise<{self.config.entity_name}[]> {{
    const response = await this.apiService.get<{{ data: Record<string, Object>[] }}>(this.endpoint);
    return response.data.map(data => {self.config.entity_name}.fromJson(data));
  }}
  
  async get{self.config.entity_name}ById(id: number): Promise<{self.config.entity_name}> {{
    const response = await this.apiService.get<{{ data: Record<string, Object> }}>(`${{this.endpoint}}/${{id}}`);
    return {self.config.entity_name}.fromJson(response.data);
  }}
  
  async create{self.config.entity_name}(entity: {self.config.entity_name}): Promise<{self.config.entity_name}> {{
    const response = await this.apiService.post<{{ data: Record<string, Object> }}>(
      this.endpoint,
      entity.toJson()
    );
    return {self.config.entity_name}.fromJson(response.data);
  }}
  
  async update{self.config.entity_name}(entity: {self.config.entity_name}): Promise<{self.config.entity_name}> {{
    const response = await this.apiService.put<{{ data: Record<string, Object> }}>(
      `${{this.endpoint}}/${{entity.id}}`,
      entity.toJson()
    );
    return {self.config.entity_name}.fromJson(response.data);
  }}
  
  async delete{self.config.entity_name}(id: number): Promise<void> {{
    await this.apiService.delete<void>(`${{this.endpoint}}/${{id}}`);
  }}
}}'''
    
    def _generate_simple_viewmodel(self) -> str:
        """Gera ViewModel simples para MVVM"""
        return f'''// viewmodels/{self.config.entity_name}ViewModel.ets

import {{ BaseViewModel }} from './base/BaseViewModel';
import {{ {self.config.entity_name} }} from '../data/models/{self.config.entity_name}';
import {{ {self.config.entity_name}Repository }} from '../data/repositories/{self.config.entity_name}Repository';

@Observed
export class {self.config.entity_name}ViewModel extends BaseViewModel {{
  @State {self.entity_name_lower}s: {self.config.entity_name}[] = [];
  @State selected{self.config.entity_name}: {self.config.entity_name} | null = null;
  
  private repository: {self.config.entity_name}Repository = new {self.config.entity_name}Repository();
  
  async load{self.entity_name_plural}(): Promise<void> {{
    await this.executeAsync(
      () => this.repository.get{self.entity_name_plural}(),
      (result) => {{
        this.{self.entity_name_lower}s = result;
      }}
    );
  }}
  
  async create{self.config.entity_name}({self._get_create_params()}): Promise<boolean> {{
    let success = false;
    const entity = new {self.config.entity_name}(0, {self._get_create_args()});
    
    await this.executeAsync(
      () => this.repository.create{self.config.entity_name}(entity),
      (result) => {{
        this.{self.entity_name_lower}s.push(result);
        success = true;
      }}
    );
    return success;
  }}
  
  async delete{self.config.entity_name}(id: number): Promise<boolean> {{
    let success = false;
    await this.executeAsync(
      () => this.repository.delete{self.config.entity_name}(id),
      () => {{
        this.{self.entity_name_lower}s = this.{self.entity_name_lower}s.filter(e => e.id !== id);
        success = true;
      }}
    );
    return success;
  }}
  
  onDestroy(): void {{
    this.{self.entity_name_lower}s = [];
    this.selected{self.config.entity_name} = null;
  }}
}}'''
    
    def _generate_simple_page(self) -> str:
        """Gera página simples para MVVM"""
        return self._generate_page()
    
    # ==========================================
    # HELPER METHODS
    # ==========================================
    
    def _get_default_value(self, prop: PropertyConfig) -> str:
        """Retorna valor padrão para propriedade"""
        if prop.name == 'id':
            return ' = 0'
        if prop.optional:
            return ''
        
        if prop.type == 'string':
            return " = ''"
        elif prop.type == 'number':
            return ' = 0'
        elif prop.type == 'boolean':
            return ' = false'
        elif prop.type == 'Date':
            return ' = new Date()'
        return ''
    
    def _generate_dto_properties(self) -> str:
        """Gera propriedades do DTO"""
        lines = []
        for prop in self.config.properties:
            optional = '?' if prop.optional else ''
            dto_type = 'string' if prop.type == 'Date' else prop.type
            lines.append(f"  {prop.name}{optional}: {dto_type};")
        return "\n".join(lines)
    
    def _generate_to_domain_mapping(self) -> str:
        """Gera mapeamento DTO -> Domain"""
        lines = []
        for prop in self.config.properties:
            if prop.type == 'Date':
                lines.append(f"      new Date(dto.{prop.name})")
            else:
                lines.append(f"      dto.{prop.name}")
        return ",\n".join(lines)
    
    def _generate_to_dto_mapping(self) -> str:
        """Gera mapeamento Domain -> DTO"""
        lines = []
        for prop in self.config.properties:
            if prop.type == 'Date':
                lines.append(f"      {prop.name}: entity.{prop.name}.toISOString()")
            else:
                lines.append(f"      {prop.name}: entity.{prop.name}")
        return ",\n".join(lines)
    
    def _get_create_params(self) -> str:
        """Gera parâmetros para método create"""
        params = []
        for prop in self.config.properties:
            if prop.name == 'id':
                continue
            optional = '?' if prop.optional else ''
            params.append(f"{prop.name}{optional}: {prop.type}")
        return ", ".join(params)
    
    def _get_create_args(self) -> str:
        """Gera argumentos para método create"""
        args = []
        for prop in self.config.properties:
            if prop.name == 'id':
                continue
            args.append(prop.name)
        return ", ".join(args)
    
    def _get_entity_creation(self) -> str:
        """Gera criação de entidade"""
        args = []
        for prop in self.config.properties:
            if prop.name == 'id':
                args.append("0")
            else:
                args.append(prop.name)
        return ", ".join(args)
    
    def _indent_code(self, text: str, level: int = 1) -> str:
        """Indenta código"""
        indent = "  " * level
        lines = text.split('\n')
        return '\n'.join(indent + line if line.strip() else line for line in lines)
