"""Verified Inferential Leap: exact shortcuts or an explicit safe fallback."""
from pythen import Reasoner


CONTRACT = [
    {'p': 'contract_voidable', 'op': 'ALL',
     'conditions': ['signer_is_minor'], 'exceptions': ['necessities_exception']},
    {'p': 'necessities_exception', 'op': 'ALL',
     'conditions': ['goods_are_essential', 'price_is_fair'], 'exceptions': []},
]


if __name__ == '__main__':
    # Hypothetical example; not a statement about any jurisdiction's law.
    reasoner = Reasoner(CONTRACT, facts=['signer_is_minor'])
    answer = reasoner.analyze('contract_voidable', method='leap')
    print('Original verdict:', answer.original_verdict)
    print('Radius:', answer.radius)
    print('Witness:', answer.witness)
    print('Execution mode:', answer.metadata['execution_mode'])
    print('Verified minimum:', reasoner.verify(answer).optimal)

    # Shared leaves prohibit independent min-plus composition.
    contradictory = Reasoner([{'p': 'p', 'op': 'ALL',
                               'conditions': ['x'], 'exceptions': ['x']}])
    fallback_answer = contradictory.analyze('p', method='leap')
    print('Shared leaf:', fallback_answer.status)
    print('Execution mode:', fallback_answer.metadata['execution_mode'])
