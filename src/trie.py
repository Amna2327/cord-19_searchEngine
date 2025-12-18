# trie.py
import pickle
from collections import defaultdict
import heapq

class TrieNode:
    def __init__(self):
        self.children = defaultdict(TrieNode)
        self.is_word = False

class Trie:
    def __init__(self):
        self.root = TrieNode()
        self.df_map = {}  # stores document frequency for ranking

    def insert(self, word, df=0):
        node = self.root
        for char in word:
            node = node.children[char]
        node.is_word = True
        self.df_map[word] = df

    def autocomplete(self, prefix, limit=5):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]

        heap = []
        def dfs(current_node, path):
            if current_node.is_word:
                term = prefix + path
                df = self.df_map.get(term, 0)
                if len(heap) < limit:
                    heapq.heappush(heap, (df, term))
                else:
                    heapq.heappushpop(heap, (df, term))
            for char, next_node in current_node.children.items():
                dfs(next_node, path + char)

        dfs(node, "")
        return [term for df, term in sorted(heap, reverse=True)]

def load_trie(trie_path, lexicon_path=None):
    """
    Load trie from pickle if available, else build from lexicon JSON.
    """
    import os
    from pathlib import Path

    trie_path = Path(trie_path)
    if trie_path.exists():
        with open(trie_path, "rb") as f:
            return pickle.load(f)

    if lexicon_path is None or not Path(lexicon_path).exists():
        raise FileNotFoundError("Lexicon file not found.")

    import json
    with open(lexicon_path, "r", encoding="utf-8") as f:
        lexicon = json.load(f)

    trie = Trie()
    for term, info in lexicon.items():
        df = info.get("df", 0)
        trie.insert(term, df=df)

    # Save pickle for next time
    os.makedirs(trie_path.parent, exist_ok=True)
    with open(trie_path, "wb") as f:
        pickle.dump(trie, f)

    return trie