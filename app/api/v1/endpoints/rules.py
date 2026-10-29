import logging
from fastapi import APIRouter, Depends
from app.core.auth import verify_internal_token
from app.schemas.rules import MagicRuleRequest, MagicRuleResponse
from app.services.rule_generator_service import RuleGeneratorService
from app.core.llm_factory import LLMFactory

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(verify_internal_token)])



@router.post("/rules/generate", response_model=MagicRuleResponse, tags=["Magic Rules"])
async def generate_magic_rules(request: MagicRuleRequest):
    """
    Translates natural language eligibility criteria into strict DNF profiles
    consumable directly by the React Back-Office visual cards.
    """
    logger.info(f"Requête de génération de règles reçue : '{request.prompt[:80]}...'")
    llm = LLMFactory.get_llm()

    result = RuleGeneratorService.generate_rules(
        prompt=request.prompt,
        context=request.context,
        llm=llm
    )

    logger.info(f"Règles générées : {len(result.profiles)} profils, succès={result.success}")
    return result
