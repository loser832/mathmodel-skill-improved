#let body-font = ("Times New Roman", "SimSun", "NSimSun", "Songti SC", "STSong")
#let song-font = ("SimSun", "NSimSun", "Songti SC", "STSong", "Times New Roman")
#let hei-font = ("Heiti SC", "STHeiti", "Songti SC", "STSong")
#let kai-font = ("KaiTi", "Kaiti SC", "STKaiti", "SimSun", "Songti SC")

#let cn-numbering(..nums) = {
  let ns = nums.pos()
  if ns.len() == 1 {
    numbering("一、", ns.at(0))
  } else if ns.len() == 2 {
    numbering("1.1", ns.at(0), ns.at(1))
  } else {
    numbering("1.1.1", ns.at(0), ns.at(1), ns.at(2))
  }
}

#set document(author: ())
#set page(
  paper: "a4",
  margin: (top: 2.5cm, bottom: 2.5cm, left: 2.5cm, right: 2.5cm),
  numbering: "1",
  number-align: center + bottom,
)
#set text(font: body-font, size: 12.05pt, lang: "zh")
#set par(
  first-line-indent: (amount: 2em, all: true),
  justify: true,
  leading: 0.72em,
  spacing: 0.35em,
)
#set heading(numbering: cn-numbering)
#set enum(numbering: "1.")
#set table(inset: 0.45em)
#show heading.where(level: 1): set align(center)
#show heading.where(level: 1): set text(size: 17.3pt, weight: "bold")
#show heading.where(level: 1): set block(above: 1.25em, below: 0.82em)
#show heading.where(level: 2): set text(size: 14.45pt, weight: "bold")
#show heading.where(level: 2): set block(above: 1.15em, below: 0.55em)
#show heading.where(level: 3): set text(size: 12.05pt, weight: "bold")
#show heading.where(level: 3): set block(above: 1.15em, below: 0.55em)
#show figure.caption: it => text(size: 12pt, weight: "bold")[#it]
#show raw: set text(size: 10pt, font: ("Courier New", "Menlo", "SimSun", "Songti SC"))
#show raw.where(block: true): set block(
  fill: luma(97%),
  stroke: 0.8pt + luma(70%),
  inset: 0.7em,
  above: 0.7em,
  below: 0.7em,
)

#let song = (body) => text(font: song-font, body)
#let hei = (body) => text(font: hei-font, weight: "bold", body)
#let kai = (body) => text(font: kai-font, body)
#let paper-title(body) = {
  align(center)[#text(size: 17.3pt, weight: "bold")[#body]]
  v(1em)
}
#let abstract-title() = align(center)[#text(size: 14pt, weight: "bold")[摘要]]
#let keywords-cn(body) = block(above: 1em)[
  #text(font: hei-font, size: 12pt, weight: "bold")[关键字：] #body
]
#let abstract-cn(body, keywords) = {
  abstract-title()
  block(above: 0.15em)[#body]
  keywords-cn(keywords)
  pagebreak()
}
#let ai-declaration(body) = [
#heading(numbering: none, outlined: false)[AI工具使用声明]
#body
]
#let references-cn() = [
#heading(numbering: none, outlined: false)[参考文献]
#{ set par(first-line-indent: 0pt, spacing: 0.35em); include("references.typ") }
]
#let appendix-cn() = [
#heading(numbering: none, outlined: false)[附录]
#include("sections/A_appendix.typ")
]

#let three-line-table(caption, columns, header, body, inset: (x: 0.35em, y: 0.52em), cell-align: center) = {
  let col-count = header.len()
  let body-rows = calc.floor(body.len() / col-count)
  let bottom-y = body-rows + 1
  let styled-header = header.map(cell => strong(cell))

  figure(
    block(width: 100%, breakable: false)[
      #align(center)[
        #box[
          #table(
          columns: columns,
          align: cell-align,
          stroke: none,
          inset: inset,
          table.hline(y: 0, stroke: 0.8pt),
          table.hline(y: 1, stroke: 0.5pt),
          table.hline(y: bottom-y, stroke: 0.8pt),
          ..styled-header,
          ..body,
          )
        ]
      ]
    ],
    kind: table,
    supplement: [表],
    caption: caption,
  )
}

#counter(page).update(1)

#paper-title[[【根据研究对象、核心方法或主要目标拟定标题，不原样照抄赛题标题】]]

#abstract-cn[
  [【按最终结果填写中文摘要：逐个子问题说明方法、模型、关键数值与结论；不插入图、表、代码块或复杂推导公式。】]
][
  [【填写 3--5 个对象/模型/方法关键词，用分号分隔，不使用软件名】]
]

#include("sections/1_restatement.typ")
#include("sections/2_analysis.typ")
#include("sections/3_assumptions.typ")
#include("sections/4_symbols.typ")
#include("sections/5_problem1.typ")
#include("sections/6_problem2.typ")
#include("sections/7_problem3.typ")
#include("sections/8_sensitivity.typ")
#include("sections/9_evaluation.typ")
#include("sections/10_conclusion.typ")

#pagebreak()
#ai-declaration[【根据实际使用情况填写官方要求的 AI 工具使用声明。】]
#pagebreak()
#references-cn()
#pagebreak()
#appendix-cn()
