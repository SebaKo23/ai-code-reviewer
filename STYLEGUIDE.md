# Python Code Styleguide & Guidelines

1. **Type Hints**: Wszystkie funkcje i metody MUSZĄ posiadać pełne typowanie argumentów oraz typu zwracanego (Type Annotations).
2. **Logging**: Kategoryczny zakaz używania `print()`. Do debugowania i logowania należy używać modułu `logging`.
3. **Error Handling**: Nie wolno używać pustych bloków `except: pass`. Każdy wyjątek musi być zalogowany lub obsłużony.
4. **Docstrings**: Wszystkie publiczne funkcje i klasy muszą posiadać docstringi w formacie Google.