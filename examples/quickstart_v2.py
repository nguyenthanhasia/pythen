"""Executable PYTHEN 2 research-framework demonstration."""
from pythen import Reasoner, Intervention

rules = [
    {"p": "contract_voidable", "op": "ALL",
     "conditions": ["signer_is_minor"], "exceptions": ["necessities_exception"]},
    {"p": "necessities_exception", "op": "ALL",
     "conditions": ["goods_are_essential", "price_is_fair"], "exceptions": []},
]

reasoner = Reasoner(rules, facts=["signer_is_minor"])
assert reasoner.evaluate("contract_voidable") is True
result = reasoner.challenge("contract_voidable")
assert result.radius == 2
assert result.witness == ("goods_are_essential", "price_is_fair")
checked = reasoner.verify(result)
assert checked.valid and checked.optimal
world = reasoner.intervene(Intervention(add=result.witness))
assert world.evaluate("contract_voidable") is False
assert reasoner.evaluate("contract_voidable") is True
print("verdict:", reasoner.evaluate("contract_voidable"))
print("radius:", result.radius)
print("witness:", result.witness)
print("verified minimum:", checked.optimal)
print("counterfactual verdict:", world.evaluate("contract_voidable"))
