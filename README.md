# Лабораторная работа № 3
- Пономарев Вадим Васильевич P33311
- `lisp -> asm | risc | harv | hw | instr | struct | stream | port | cstr | prob1 | pipeline`

## Форма Бэкуса — Наура

```
program ::= <section_text> <section_data> | <section_data> <section_text> | <section_text>

<section_data> ::= "section .data:" <variables>

<section_text> ::= "section .text:" <instructions>

<variables> ::= (<variable> | (<int> | <string>))

<instructions> ::= (<label> | <instruction>)

<name> ::= [a-zA-Z]+

<label> ::= "."<name> ":"

<variable> ::= <name> ":"

<reg=> ::= "r1" | "r2" | "r3" | "r4" | "r5"

<string> ::= '"' <character>, { <character> | <underscore> | " " } '"'

<char> ::= "'" ( <character> | "\0" | "\n" ) "'"

<int> ::= <digit>, { <digit> }

<digit> ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"

<register_var_name> ::= <reg> ", " "(" <name> ")"

<var_name_register> ::=  "(" <name> ")" ", " <reg>

operation_3_args ::= ("ADD" | "SUB" | "DIV" | "MOD" | "MUL") " " ((<reg> ", " <reg> ", " <value>) | (<reg> ", " <reg> ", " <reg>))

operation_2_args ::= ("CMP" | "LD" | "ST" | "MOV") " " ((<reg> ", " <reg>) | (<reg> ", " "(" <name> ")") | ("(" <name> ")" ", " <reg>))

operation_1_arg ::= ("JMP" | "JE" | "JNE" | "JG" | "INC" | "DEC") " " (<label> | <reg>)

operation_0_args ::= ("HLT" | "NOP")

<instruction> ::= <operation_3_args> | <operation_2_args> | <operation_1_arg> | <operation_0_args>
```

## Модель процессора

### Схема

![scheme.jpg](doc%2Fscheme.jpg)