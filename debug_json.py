import json
import re

def _repair_json(json_str: str) -> str:
    """Attempts to repair common JSON errors, specifically unescaped backslashes."""
    # Replace unescaped backslashes that are NOT part of a valid escape sequence.
    # Valid escapes: \" \\ \/ \b \f \n \r \t \uXXXX
    # Regex: \\(?![/\"\\bfnrtu])
    return re.sub(r'\\(?![/\"\\bfnrtu])', r'\\\\', json_str)

def test_parsing():
    # The failing string from the user log
    # Note: I am using a raw string here to simulate exactly what the python code receives
    # The user log shows:
    #      {
    #        "tool": "search_text",
    #        "args": {
    #          "pattern": "<script>[\s\S]*?</script>",
    #          "path": "D:\\Projects\\Javacript\\Landing\\index.html",
    #          "regex": true,
    #          "case_sensitive": false,
    #          "max_results": 500
    #        }
    #      }
    
    # In the log, "[\s\S]" contains a backslash.
    # "D:\\Projects" contains two backslashes.
    
    raw_content = r"""
     {
       "tool": "search_text",
       "args": {
         "pattern": "<script>[\s\S]*?</script>",
         "path": "D:\\Projects\\Javacript\\Landing\\index.html",
         "regex": true,
         "case_sensitive": false,
         "max_results": 500
       }
     }
    """
    
    print(f"Original content:\n{raw_content}")
    
    # Test 1: Direct JSON load (expected to fail)
    try:
        json.loads(raw_content)
        print("Test 1: Direct JSON load SUCCESS (Unexpected)")
    except json.JSONDecodeError as e:
        print(f"Test 1: Direct JSON load FAILED as expected: {e}")

    # Test 2: Repair logic
    repaired = _repair_json(raw_content)
    print(f"\nRepaired content:\n{repaired}")
    
    try:
        data = json.loads(repaired)
        print("Test 2: Repaired JSON load SUCCESS")
        print(json.dumps(data, indent=2))
    except json.JSONDecodeError as e:
        print(f"Test 2: Repaired JSON load FAILED: {e}")

if __name__ == "__main__":
    test_parsing()
