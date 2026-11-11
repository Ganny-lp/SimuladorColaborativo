"""Constraints for editable decisions; arbitrary custom inputs may be signed."""
import math
from backend.domain.entities.node import Node, NodeCategory
from backend.domain.exceptions import InvalidModelError

FRACTIONS = {'Carga_Tributaria','Margem_Alvo','Taxa_Reinvestimento','Alfa','Inovacao_Fabricantes'}
INTEGERS = {'Numero_Tecnicos','Nc','Prazo','Estoque_Alvo','Estoque_Inicial','Base_Instalada_Inicial'}
POSITIVE = {'Prazo','Preco_Equipamento_Novo','Complexidade_Reparo','Base_Instalada_Inicial'}

def validate_input(node: Node, value: float) -> float:
    if node.category is not NodeCategory.INPUT or node.has_expression:
        raise InvalidModelError('A variável não é uma entrada editável.')
    value = float(value)
    if not math.isfinite(value):
        raise InvalidModelError('Informe um número finito.')
    if node.name in FRACTIONS and not 0 <= value <= 1:
        raise InvalidModelError('Informe uma fração entre 0 e 1.')
    if node.name in POSITIVE and value <= 0:
        raise InvalidModelError('Informe um valor maior que zero.')
    if node.name in INTEGERS and not value.is_integer():
        raise InvalidModelError('Informe um número inteiro.')
    # Shipped monetary/count inputs never accept negative values.
    if node.name in NONNEGATIVE and value < 0:
        raise InvalidModelError('Informe um valor não negativo.')
    if node.name in {'Juros_Base','Inflacao'} and not 0 <= value <= 1:
        raise InvalidModelError('Informe uma taxa entre 0 e 1.')
    return value

NONNEGATIVE = FRACTIONS | INTEGERS | POSITIVE | {
    'Pt','Cp','C_Mao_Obra','Logistica_Unitario','Prazo_Fornecedor','Beta_1','Cap',
    'Emprestimo','budget_update','budget_training','budget_infra','budget_promo',
    'Despesas','Pró-Labore','Salarios_Beneficios','Servicos_Terceiros_Consultoria',
    'Manutencao','Custos_Legalizacao','Maquinas_Equipamentos','Recursos_Tecnologicos',
    'Infra_Reforma','Marketing_Abertura','Mobiliario','Caixa_Reserva','Influencia_Avaliacoes_Online',
}
