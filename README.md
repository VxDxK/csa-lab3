# Лабораторная работа № 3

- Пономарев Вадим Васильевич P33311
- `lisp -> asm | risc | harv | hw | instr | struct | stream | port | cstr | prob1 | pipeline`
- С упрощением

## Язык программирования


### Синтаксис

```
program ::= <section_text> <section_data> | <section_data> <section_text> | <section_text>
<section_data> ::= "section .data:" <variables>
<section_text> ::= "section .text:" <instructions>
<variables> ::= (<variable> | (<int> | <string>))
<instructions> ::= (<label> | <instruction>)
<name> ::= [a-zA-Z]+
<label> ::= "."<name> ":"
<variable> ::= <name> ":"
<reg=> ::= "r1" | "r2" | "r3" | "r4" | "r5" | "r6" | "r7" | "r8 | "r9" | "r10" | "r11" | "r12" | "r14" | "r15""
<string> ::= '"' <character>, { <character> | <underscore> | " " } '"'
<char> ::= "'" ( <character> | "\0" | "\n" ) "'"
<int> ::= <digit>, { <digit> }
<digit> ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
bin_ops ::= ("CMP" | "LD" | "ST" | "MOV" | "ADD" | "CMP" | "DIV") " " ((<reg> ", " <reg>) | (<reg> ", " "(" <name> ")") | ("(" <name> ")" ", " <reg>))
un_ops ::= ("INC" | "DEC" | "NEGR") " "  (<reg>)
branch ::= ("JMP" | "JE" | "JG") " " (<label>)
zero_arg ::= ("HLT" | "NOP")
<instruction> ::= <bin_ops> | <un_ops> | branch | <zero_arg>
```

### Описание
- Поддержка строковых и числовых литералов
- Переменные объявляются в секции `.data`, инструкции в секции `.text`
- Точка входа объявляется меткой `.start`

### Набор инструкции

```
MOV reg, reg
LD reg, [reg]
ST [reg], reg
INC reg
DEC reg
NEGR reg
ADD reg, reg
DIV reg, reg
MOD reg, reg
CMP reg, reg
JUMP label
JG label
JE lebel
IN reg, port
OUT port, reg
HLT
NOP
```

### Пример программы выводящий `Hello world!`
```
section .data
    hello_str: "hello, world!"
section .text
.start:
    MOV r2, 0
    MOV r1, hello_str
.reload:
    LD r3, [r1]
    CMP r2, r3
    JE .exit
    OUT 1, r3
    INC r1
    JMP .reload
.exit:
    HLT
```

Компилируется в `JSON` следующего формата:
```json
{
    "data_mem": {
        "0": 104,
        "1": 101,
        "2": 108,
        "3": 108,
        "4": 111,
        "5": 32,
        "6": 119,
        "7": 111,
        "8": 114,
        "9": 108,
        "10": 100,
        "11": 33,
        "12": 0
    },
    "start": 0,
    "code_mem": {
        "0": {
            "opcode": "mov",
            "args": [
                "r2",
                "0"
            ]
        },
        "1": {
            "opcode": "mov",
            "args": [
                "r1",
                "0"
            ]
        },
        "2": {
            "opcode": "ld",
            "args": [
                "r3",
                "r1"
            ]
        },
        "3": {
            "opcode": "cmp",
            "args": [
                "r2",
                "r3"
            ]
        },
        "4": {
            "opcode": "je",
            "args": [
                "8"
            ]
        },
        "5": {
            "opcode": "out",
            "args": [
                "1",
                "r3"
            ]
        },
        "6": {
            "opcode": "inc",
            "args": [
                "r1"
            ]
        },
        "7": {
            "opcode": "jmp",
            "args": [
                "2"
            ]
        },
        "8": {
            "opcode": "hlt",
            "args": []
        }
    }
}
```

- data_mem - память данных
- code_mem - память инструкций
- start - точка входа в памяти инструкций


## Организация памяти:
Гарвардская архитектура, память данных и память команд разделена.
Данные и инструкции располагаются в начале соответствующих себе адресных пространств.
При инициализации процессора `r15` устанавливается на последний адрес памяти данных.

### Память данных
Массив 32-х битных слов, реализуется используя `list[int]`.
При старте симуляции инициализируется нулевыми значениями.

- Строковые литералы выделяются статически при компиляции в c-style.

### Память команд
Реализуется с использованием `list[Instruction]`.
При старте симуляции инициализируется `NOP` инструкциями.

### Регистры
`r1 r2 r3 r4 r5 r6 r7 r8 r9 r10 r11 r12  r14 r15` - общего назначения. При инициализации `r15` устанавливается в конец памяти данных, что позволяет программисту работать с ним как со стеком используя `INC` и `DEC`.


## Транслятор
- Формат запуска: `./translator.py hello_user.vasm hello_user.json`
Реализован в [translator.py](translator.py).
- Проходом по секции `.data` преобразовывает её в словарь `переменная -> адрес в памяти данных`.
- Первым проходом по секции `.text` получает словарь `метка -> адрес в памяти команд`.
- Вторым проходом по секции `.text` резолвит все переменные и метки используя словари полученные на этапах выше.

## Модель процессора
- Формат запуска: ` ./machine.py hello_user.json ./my_name`. Имя файла с входными данными можно опустить если в них нет нужды.
Реализована в [machine.py](machine.py)
### Схема
![scheme.jpg](doc%2Fscheme.jpg)

- choose port - выбор порта для работы с IO
- write io - запись в выбранное устройство
- read io чтение с выбранного устройства
- choose op - выбор операции на АЛУ
- latch reg - защелкнуть регистр
- sel regs - выбор в мультиплексорe
- sel ip - выбор в мультиплексоре регистра IP
- write data - запись в память данных
- read data - чтение памяти данных
- read instruction - чтение памяти инструкций

## Тестирование
Тестирование производится набором **golden** тестов, реализация в директории: [tests](tests).
Тестируются следующие алгоритмы:
- cat
- hello
- hello_user_name
- prob1

Исходные коды алгоритмов находятся в: 
[sources](examples/sources)

## Статка

|             ФИО            |       алг       | LoC | code байт | code инстр. | инстр. | такт. |                                               вариант                                               |
|:--------------------------:|:---------------:|:---:|:---------:|:-----------:|:------:|:-----:|:---------------------------------------------------------------------------------------------------:|
| Пономарев Вадим Васильевич |       cat       |  11 |           |      7      |   50   |  148  | lisp -> asm \| risc \| harv \| hw \| instr \| struct \| stream \| port \| cstr \| prob1 \| pipeline |
| Пономарев Вадим Васильевич |      hello      |  15 |           |      9      |   78   |  246  | lisp -> asm \| risc \| harv \| hw \| instr \| struct \| stream \| port \| cstr \| prob1 \| pipeline |
| Пономарев Вадим Васильевич | hello_user_name |  42 |           |      30     |   803  |  2548 | lisp -> asm \| risc \| harv \| hw \| instr \| struct \| stream \| port \| cstr \| prob1 \| pipeline |
| Пономарев Вадим Васильевич |      prob1      |  49 |           |      39     |  11688 | 32620 | lisp -> asm \| risc \| harv \| hw \| instr \| struct \| stream \| port \| cstr \| prob1 \| pipeline |