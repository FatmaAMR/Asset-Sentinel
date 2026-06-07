from fastapi import APIRouter, HTTPException
from  services.QueryingLogic import QueryingLogic
from utils.helpers import SQL_SYSTEM_TEMPLATE, CURRENT_DATABASE_SCHEMA
from db.connection import DatabaseManager

# 1. Define the router first
router = APIRouter()

# 2. Initialize your logic and DB manager
logic = QueryingLogic()
db_manager = DatabaseManager()

# 3. Now you can use @router
@router.get("/ask")
async def ask_question(question: str):
    formatted_instruction = SQL_SYSTEM_TEMPLATE.format(schema=CURRENT_DATABASE_SCHEMA)
    
    sql_query = await logic.get_llm_response(
        system_instruction=formatted_instruction,
        user_input=question
    )
    
    if not sql_query:
        raise HTTPException(status_code=500, detail="Failed to generate SQL query")

    # Strip markdown code fences
    import re
    sql_query = re.sub(r"```(?:sql)?\s*", "", sql_query).strip()

    try:
        data = db_manager.execute_query(sql_query)
        return {
            "status": "success",
            "question": question,
            "sql": sql_query,
            "results": data
        }
    except Exception as e:
        return {
            "status": "db_error",
            "sql": sql_query,
            "error": str(e)
        }