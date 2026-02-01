# code-generator-arkts

# Clean Architecture com cache e validações
python -m generator.cli generate User \
  --props "name:string,email:string,age:number" \
  --cache \
  --validation

# MVVM Tradicional simples
python -m generator.cli g Product \
  --arch mvvm \
  --props "name:string,price:number"

# Propriedades opcionais
python -m generator.cli g User \
  --props "name:string,bio:string?"

# Especificar diretório de saída
python -m generator.cli g Order \
  --props "userId:number,total:number" \
  --output ./src/features/orders

# Interactive
python -m generator.cli interactive