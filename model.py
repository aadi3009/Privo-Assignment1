from transformers import AutoModelForTokenClassification
from labels import LABEL2ID, ID2LABEL


def freeze_lower_layers(model, num_layers_to_freeze: int = 1):
    """
    Freeze lower layers safely across architectures (BERT, RoBERTa, DistilBERT).
    If architecture is unknown, silently skip without crashing.
    """

    # 1. Try standard BERT/Roberta path → model.{base}.encoder.layer
    base = getattr(model, model.base_model_prefix, None)
    if base is not None:
        # BERT-like
        encoder = getattr(base, "encoder", None)
        if encoder is not None and hasattr(encoder, "layer"):
            layers = encoder.layer
            num = min(num_layers_to_freeze, len(layers))
            for layer in layers[:num]:
                for param in layer.parameters():
                    param.requires_grad = False
            return
    
        # DistilBERT-like
        transformer = getattr(base, "transformer", None)
        if transformer is not None and hasattr(transformer, "layer"):
            layers = transformer.layer
            num = min(num_layers_to_freeze, len(layers))
            for layer in layers[:num]:
                for param in layer.parameters():
                    param.requires_grad = False
            return

    # If architecture is unknown → do nothing (safe no-op)
    print("⚠ freeze_lower_layers: Unknown architecture, skipping layer freezing safely.")


def create_model(model_name: str, dropout: float = 0.2, freeze_layers: int = 1):
    """
    Create a token classification model with:
    - Label mappings
    - Slightly higher dropout for better generalization
    - Optional lower-layer freezing (now architecture-safe)
    """
    model = AutoModelForTokenClassification.from_pretrained(
        model_name,
        num_labels=len(LABEL2ID),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )

    # Set dropout safely
    for attr in ["hidden_dropout_prob", "attention_probs_dropout_prob", "dropout"]:
        if hasattr(model.config, attr):
            setattr(model.config, attr, dropout)

    # Apply freezing (optional)
    if freeze_layers > 0:
        freeze_lower_layers(model, num_layers_to_freeze=freeze_layers)

    return model
