# Other diagram types

Minimal, copy-paste templates. Each goes in a ```mermaid fenced block. Full docs: https://mermaid.js.org

## Sequence diagram

Interactions over time between participants.

```mermaid
sequenceDiagram
    participant U as User
    participant S as Server
    U->>S: Request
    S-->>U: Response
    Note over U,S: dashed arrow = reply
    alt success
        S->>S: log ok
    else error
        S->>S: log error
    end
```

Arrows: `->>` solid, `-->>` dashed reply, `-x` lost message, `->>+`/`->>-` activate/deactivate.

## State diagram

State machines.

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Running: start
    Running --> Idle: stop
    Running --> [*]: kill
```

## Class diagram

```mermaid
classDiagram
    class Animal {
        +String name
        +eat()
    }
    class Dog
    Animal <|-- Dog : inherits
```

Relations: `<|--` inheritance, `*--` composition, `o--` aggregation, `-->` association, `..>` dependency.

## Entity relationship

```mermaid
erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ LINE_ITEM : contains
    CUSTOMER {
        string name
        string email
    }
```

Cardinality: `||` one, `o{` zero-or-many, `|{` one-or-many.

## Gantt

```mermaid
gantt
    title Project
    dateFormat YYYY-MM-DD
    section Phase 1
    Spec       :a1, 2026-06-01, 5d
    Build      :after a1, 10d
```

## Pie

```mermaid
pie title Share
    "A" : 45
    "B" : 30
    "C" : 25
```

## Mindmap

```mermaid
mindmap
  root((Topic))
    Branch A
      Leaf 1
      Leaf 2
    Branch B
```

## Git graph

```mermaid
gitGraph
    commit
    branch feature
    checkout feature
    commit
    checkout main
    merge feature
```

## Timeline

```mermaid
timeline
    title History
    2024 : Founded
    2025 : Series A : First hire
    2026 : Launch
```

## Quadrant chart

```mermaid
quadrantChart
    title Effort vs Impact
    x-axis Low Effort --> High Effort
    y-axis Low Impact --> High Impact
    "Task A": [0.3, 0.8]
    "Task B": [0.7, 0.2]
```
