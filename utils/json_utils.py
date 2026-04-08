import json

class ResultProcessor:
    @staticmethod
    def extract_json(s):
        # """Extract JSON from string"""
        starts = [i for i, c in enumerate(s) if c in {"{", "["}]
        
        for start in starts:
            for end in range(len(s) - 1, start - 1, -1):
                if s[end] in {"}", "]"}:
                    candidate = s[start:end + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        continue
        # raise ValueError("No valid JSON found in string")
        # 正则匹配 ***{...}*** 中的内容（非贪婪模式）
        # try:
        #     matches = re.findall(r'\*{3}(\{.*?\})\*{3}', s)
        #     data = json.loads(matches[0])
        # except:
        #     print(s)
        #     return ""
        # return data
    
    @staticmethod
    def save_results(results, filename):
        """Save results to JSON file"""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)


