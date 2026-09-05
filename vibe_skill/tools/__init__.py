"""
Package vibe_skill.tools — squelette non connecté (voir legifrance_vibe.py).

Esquisse une normalisation au-dessus des outils natifs de Vibe, web_search
(paramètre query) et web_fetch (paramètre url). Les fonctions de ce package
ne les appellent pas réellement : voir l'avertissement dans
legifrance_vibe.py avant tout usage.

Utiliser directement web_search / web_fetch (voir SKILL.md) plutôt que ce
package, sauf à l'avoir d'abord complété.
"""

__version__ = "1.0.0"
__all__ = ["legifrance_vibe"]
