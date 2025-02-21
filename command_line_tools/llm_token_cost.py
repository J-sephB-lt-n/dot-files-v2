#!/usr/bin/env python3
"""
Example usage:
$ llm_token_cost openai gpt-4o --in=69 --out=0

Place this script (without .py) in /usr/local/bin/ to make this script globally available
(might also need `sudo chmod +x /usr/local/bin/llm_token_cost`
"""

import argparse
import datetime
from collections import namedtuple
from typing import Final

ExpiringData = namedtuple(
    "ExpiringData",
    ["last_updated_date", "value"],
)

ZAR_PER_USD: Final[ExpiringData] = ExpiringData(
    last_updated_date=datetime.date(2025, 2, 21),
    value=18.39,
)

COST_PER_MILLION_TOKENS: Final[dict] = {
    "openai": {
        # https://openai.com/api/pricing/
        "gpt-4o": {
            "input": ExpiringData(
                last_updated_date=datetime.date(2025, 1, 30), value=2.5
            ),
            "output": ExpiringData(
                last_updated_date=datetime.date(2025, 1, 30), value=10
            ),
        },
        "gpt-4o-mini": {
            "input": ExpiringData(
                last_updated_date=datetime.date(2025, 1, 30), value=0.15
            ),
            "output": ExpiringData(
                last_updated_date=datetime.date(2025, 1, 30), value=0.6
            ),
        },
    },
    "anthropic": {
        # https://www.anthropic.com/pricing#anthropic-api
        "claude-3-5-sonnet": {
            "input": ExpiringData(
                last_updated_date=datetime.date(2025, 1, 30), value=3
            ),
            "output": ExpiringData(
                last_updated_date=datetime.date(2025, 1, 30), value=15
            ),
        },
        "claude-3-haiku": {
            "input": ExpiringData(
                last_updated_date=datetime.date(2025, 1, 30), value=0.25
            ),
            "output": ExpiringData(
                last_updated_date=datetime.date(2025, 1, 30), value=1.25
            ),
        },
    },
    "google": {
        # https://ai.google.dev/pricing
        "gemini-1.5-flash": {
            "input": ExpiringData(
                last_updated_date=datetime.date(2025, 1, 30), value=0.075
            ),
            "output": ExpiringData(
                last_updated_date=datetime.date(2025, 1, 30), value=0.3
            ),
        },
        "gemini-1.5-pro": {
            "input": ExpiringData(
                last_updated_date=datetime.date(2025, 2, 21), value=1.25
            ),
            "output": ExpiringData(
                last_updated_date=datetime.date(2025, 2, 21), value=5
            ),
        },
    },
}

if __name__ == "__main__":
    available_models: list[str] = []
    for model_provider in COST_PER_MILLION_TOKENS:
        for model_name in COST_PER_MILLION_TOKENS[model_provider]:
            available_models.append(f"{model_provider} {model_name}")
    arg_parser = argparse.ArgumentParser(
        description=f"Available models: {available_models}"
    )
    arg_parser.add_argument("model_provider")
    arg_parser.add_argument("model_name")
    arg_parser.add_argument(
        "-i", "--input_tokens", help="Number of input tokens", type=int, default=0
    )
    arg_parser.add_argument(
        "-o", "--output_tokens", help="Number of output tokens", type=int, default=0
    )
    args = arg_parser.parse_args()
    if args.model_provider not in COST_PER_MILLION_TOKENS:
        print(
            f"Provider '{args.model_provider}' not found. Available model providers are "
            + str(list(COST_PER_MILLION_TOKENS.keys()))
        )
        exit()

    model_costs: dict = COST_PER_MILLION_TOKENS[args.model_provider]
    if args.model_name not in model_costs:
        print(
            f"Model '{args.model_name}' not found for provider '{args.model_provider}'. Available models are "
            + str(list(model_costs.keys()))
        )
        exit()

    model_cost = model_costs[args.model_name]

    print("Model provider: ", args.model_provider)
    print("Model:          ", args.model_name)
    print(
        f"Assuming an USD/ZAR exchange rate of $1 = R{ZAR_PER_USD.value:.2f}. (this was last updated {ZAR_PER_USD.last_updated_date})"
    )
    if args.input_tokens > 0:
        usd_cost: float = args.input_tokens * model_cost["input"].value / 1_000_000
        zar_cost: float = usd_cost * ZAR_PER_USD.value
        print(
            f'The cost of {args.input_tokens:,} input tokens is ${usd_cost:,.8f} ~= R{zar_cost:,.8f} (model inference prices last updated at {model_cost["input"].last_updated_date})'
        )

    if args.output_tokens > 0:
        usd_cost: float = args.output_tokens * model_cost["output"].value / 1_000_000
        zar_cost: float = usd_cost * ZAR_PER_USD.value
        print(
            f'The cost of {args.output_tokens:,} output tokens is ${usd_cost:,.8f} ~= R{zar_cost:,.8f} (model inference prices last updated at {model_cost["output"].last_updated_date})'
        )
