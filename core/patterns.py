"""Controlled list of common mistake patterns for Korean speakers of English.

The AI must classify mistakes using these keys (or "other:<slug>").
"""

from __future__ import annotations

import re
from dataclasses import dataclass

CATEGORIES: tuple[str, ...] = (
    "preposition", "article", "tense", "word_choice", "konglish",
    "politeness", "collocation", "grammar_other", "pronunciation", "fluency",
)

_OTHER_RE = re.compile(r"^other:[a-z0-9_\-]{2,40}$")


@dataclass(frozen=True)
class Pattern:
    key: str
    label_ko: str
    label_en: str
    description_ko: str
    example_wrong: str
    example_right: str

    @property
    def category(self) -> str:
        return self.key.split(":", 1)[0]


# (key, label_ko, label_en, description_ko, example_wrong, example_right)
_RAW: list[tuple[str, str, str, str, str, str]] = [
    # --- preposition ---
    ("preposition:until_vs_by", "마감일에 until 사용", "until vs. by for deadlines",
     "마감 시점에는 by, 상태가 계속될 때는 until을 씁니다.",
     "Please send it until Friday.", "Please send it by Friday."),
    ("preposition:in_on_at_time", "시간 전치사 in/on/at 혼동", "in/on/at with time",
     "요일·날짜는 on, 시각은 at, 월·연도는 in을 씁니다.",
     "The meeting is in Monday at 3 p.m.", "The meeting is on Monday at 3 p.m."),
    ("preposition:discuss_about", "discuss 뒤의 불필요한 about", "'discuss about'",
     "discuss는 about 없이 바로 목적어를 받습니다.",
     "Let's discuss about the audit plan.", "Let's discuss the audit plan."),
    ("preposition:contact_to", "contact 뒤의 불필요한 to", "'contact to'",
     "contact는 to 없이 바로 사람을 목적어로 받습니다.",
     "I will contact to the client today.", "I will contact the client today."),
    ("preposition:reply_me", "reply 뒤의 to 누락", "'reply me'",
     "reply는 'reply to + 사람/메일' 형태로 씁니다.",
     "Please reply me by today.", "Please reply to me by today."),
    ("preposition:arrive_to", "arrive to 사용", "'arrive to'",
     "도착할 때는 arrive at(건물·지점), arrive in(도시·국가)을 씁니다.",
     "We arrived to the client's office at 9.", "We arrived at the client's office at 9."),
    ("preposition:attend_to_meeting", "attend 뒤의 불필요한 to", "'attend to the meeting'",
     "회의에 참석하다는 attend the meeting입니다. attend to는 '처리하다'라는 뜻이에요.",
     "I will attend to the kickoff meeting.", "I will attend the kickoff meeting."),
    # --- article ---
    ("article:missing_the", "정관사 the 누락", "Missing 'the'",
     "서로 알고 있는 특정한 대상 앞에는 the를 씁니다.",
     "I sent report to client yesterday.", "I sent the report to the client yesterday."),
    ("article:missing_a", "부정관사 a/an 누락", "Missing 'a/an'",
     "셀 수 있는 단수 명사에는 a/an이 필요합니다.",
     "She is senior auditor.", "She is a senior auditor."),
    ("article:unneeded_the", "불필요한 the", "Unnecessary 'the'",
     "연도나 일반적인 개념 앞에는 the를 쓰지 않습니다.",
     "I joined the firm in the 2022.", "I joined the firm in 2022."),
    # --- grammar_other ---
    ("grammar_other:explain_me", "explain me 구조", "'explain me'",
     "explain은 'explain + 내용 + to + 사람' 순서로 씁니다.",
     "Could you explain me the adjustment?", "Could you explain the adjustment to me?"),
    ("grammar_other:i_am_agree", "I'm agree", "'I'm agree'",
     "agree는 동사이므로 be동사와 함께 쓰지 않습니다.",
     "I'm agree with your proposal.", "I agree with your proposal."),
    ("grammar_other:uncountable_plural", "불가산명사의 복수형", "Plural of uncountable nouns",
     "information, advice, feedback, equipment에는 -s를 붙이지 않습니다.",
     "Please send me the informations.", "Please send me the information."),
    ("grammar_other:subject_verb_agreement", "주어-동사 수 일치", "Subject-verb agreement",
     "3인칭 단수 주어 뒤의 현재형 동사에는 -s를 붙입니다.",
     "The client have three factories.", "The client has three factories."),
    ("grammar_other:missing_subject", "주어 생략", "Missing subject",
     "영어 문장에는 주어가 필요합니다. 필요하면 형식상 주어 it을 씁니다.",
     "Is difficult to finish by Friday.", "It is difficult to finish by Friday."),
    ("grammar_other:question_word_order", "간접의문문 어순", "Indirect question word order",
     "간접의문문은 '의문사 + 주어 + 동사' 순서입니다.",
     "Can you tell me when is the deadline?", "Can you tell me when the deadline is?"),
    ("grammar_other:look_forward_to_ing", "look forward to 뒤 동사원형", "'look forward to' + verb",
     "look forward to 뒤에는 -ing 형태를 씁니다.",
     "I look forward to hear from you.", "I look forward to hearing from you."),
    # --- tense ---
    ("tense:present_perfect_misuse", "과거 시점과 현재완료 혼용", "Present perfect with past time",
     "yesterday, last week처럼 끝난 시점이 있으면 단순과거를 씁니다.",
     "I have sent the file yesterday.", "I sent the file yesterday."),
    ("tense:since_with_present", "since와 현재시제", "'since' with present tense",
     "과거부터 지금까지 계속되는 일은 현재완료(진행)를 씁니다.",
     "I am working here since 2022.", "I have been working here since 2022."),
    ("tense:present_for_past", "과거 일에 현재형 사용", "Present tense for past events",
     "이미 끝난 일은 과거형으로 말합니다.",
     "Yesterday I send the file to the client.", "Yesterday I sent the file to the client."),
    ("tense:future_with_will_overuse", "시간 부사절의 will", "'will' in time clauses",
     "when, after, before, once가 이끄는 절에서는 미래라도 현재형을 씁니다.",
     "I will send it after I will check it.", "I will send it after I check it."),
    # --- word_choice ---
    ("word_choice:make_vs_do", "make와 do 혼동", "make vs. do",
     "decision, plan, request, mistake는 make와 함께 씁니다.",
     "We need to do a decision today.", "We need to make a decision today."),
    ("word_choice:say_vs_tell", "say와 tell 혼동", "say vs. tell",
     "tell은 듣는 사람을 바로 목적어로 받고, say는 받지 않습니다.",
     "He said me that the file is ready.", "He told me that the file is ready."),
    ("word_choice:borrow_vs_lend", "borrow와 lend 혼동", "borrow vs. lend",
     "빌려 받으면 borrow, 빌려 주면 lend입니다.",
     "Can you borrow me your charger?", "Can you lend me your charger?"),
    ("word_choice:check_vs_review", "check와 review 구분", "check vs. review",
     "간단한 확인은 check, 내용을 꼼꼼히 검토할 때는 review를 씁니다.",
     "Could you check the contract and give us detailed comments?",
     "Could you review the contract and give us detailed comments?"),
    ("word_choice:schedule_vs_plan", "특정 일정을 미룰 때 schedule 사용", "Postponing 'the schedule'",
     "특정 회의나 업무를 미룰 때는 그 일 자체를 목적어로 씁니다.",
     "We need to delay the schedule of the meeting.", "We need to postpone the meeting."),
    # --- konglish ---
    ("konglish:claim", "클레임 = claim?", "Konglish 'claim'",
     "불만 제기는 complaint / raise a concern입니다. claim은 '청구·주장'이에요.",
     "The client made a claim about our fee.", "The client raised a concern about our fee."),
    ("konglish:nego", "네고 = nego?", "Konglish 'nego'",
     "nego는 영어가 아닙니다. negotiate / negotiation을 씁니다.",
     "Let's nego the fee.", "Let's negotiate the fee."),
    ("konglish:sign", "사인 = sign?", "Konglish 'sign'",
     "명사 '서명'은 signature, 동사 '서명하다'는 sign입니다.",
     "Please put your sign here.", "Please put your signature here."),
    ("konglish:spec", "스펙 = spec?", "Konglish 'spec'",
     "사람의 경력·자격은 qualifications, background입니다. spec은 제품 사양이에요.",
     "He has a good spec for the job.", "He has strong qualifications for the job."),
    ("konglish:service", "서비스 = 무료?", "Konglish 'service'",
     "무료로 제공하는 것은 free of charge / complimentary입니다.",
     "This extra analysis is service.", "This extra analysis is free of charge."),
    ("konglish:handphone", "핸드폰", "Konglish 'handphone'",
     "휴대전화는 mobile phone, cell phone 또는 phone입니다.",
     "Please call my handphone.", "Please call my mobile."),
    ("konglish:fighting", "화이팅", "Konglish 'fighting'",
     "응원할 때는 Good luck! 또는 You've got this!라고 합니다.",
     "Fighting for the presentation!", "Good luck with the presentation!"),
    ("konglish:meeting_jabda", "미팅을 잡다", "'catch a meeting'",
     "회의를 잡을 때는 set up / schedule / arrange a meeting을 씁니다.",
     "Can we catch a meeting tomorrow?", "Can we set up a meeting tomorrow?"),
    ("konglish:one_shot", "원샷", "Konglish 'one shot'",
     "'원샷'은 Bottoms up! 또는 drink it in one go라고 합니다.",
     "One shot!", "Bottoms up!"),
    ("konglish:notebook", "노트북", "Konglish 'notebook'",
     "노트북 컴퓨터는 laptop입니다. notebook은 공책이에요.",
     "I left my notebook at the client's office.", "I left my laptop at the client's office."),
    # --- politeness ---
    ("politeness:too_direct_must", "must의 과도한 사용", "'must' sounds too direct",
     "요청할 때 must는 명령처럼 들립니다. could you, we need를 사용하세요.",
     "You must send the documents today.", "Could you send the documents today?"),
    ("politeness:imperative_request", "명령문으로 요청", "Requests as commands",
     "요청은 Could you / Would you mind로 부드럽게 시작합니다.",
     "Send me the bank statements.", "Could you send me the bank statements?"),
    ("politeness:blunt_no", "직설적인 거절", "Blunt refusal",
     "거절할 때는 이유와 대안을 함께 말합니다.",
     "No, we can't do that.", "Unfortunately, that would be difficult, but one option is..."),
    ("politeness:missing_softener", "완충 표현 부족", "Missing softeners",
     "I think, might, it seems로 지적을 부드럽게 합니다.",
     "Your numbers are wrong.", "I think there might be an issue with these numbers."),
    # --- collocation ---
    ("collocation:meet_a_deadline", "마감을 '지키다'", "'keep a deadline'",
     "마감을 지키다는 meet a deadline입니다.",
     "We will keep the deadline.", "We will meet the deadline."),
    ("collocation:make_an_effort", "노력을 '하다'", "'do an effort'",
     "노력하다는 make an effort / make every effort입니다.",
     "We will do our best effort.", "We will make every effort."),
    ("collocation:raise_an_issue", "이슈를 '제기하다'", "Raising an issue",
     "이슈를 제기하다는 raise an issue / flag an issue입니다.",
     "I want to suggest an issue about the inventory.",
     "I'd like to raise an issue about the inventory."),
    # --- pronunciation ---
    ("pronunciation:f_p", "f/p 구분", "f vs. p",
     "f는 윗니를 아랫입술에 살짝 대고 바람을 내보냅니다.",
     "fiscal → 'piscal'", "fiscal: /f/ 윗니 + 아랫입술"),
    ("pronunciation:v_b", "v/b 구분", "v vs. b",
     "v는 윗니를 아랫입술에 대고 성대를 울립니다.",
     "value → 'balue'", "value: /v/ 윗니 + 아랫입술 + 울림"),
    ("pronunciation:r_l", "r/l 구분", "r vs. l",
     "r은 혀가 입천장에 닿지 않고, l은 혀끝이 윗니 뒤에 닿습니다.",
     "revenue → 'levenue'", "revenue: /r/ 혀를 띄운 채 발음"),
    ("pronunciation:th", "th 발음", "th sounds",
     "혀끝을 윗니와 아랫니 사이에 살짝 넣고 발음합니다.",
     "three → 'tree'", "three: /θ/ 혀끝을 이 사이에"),
    ("pronunciation:z_j", "z/j 구분", "z vs. j",
     "z는 ㅈ이 아니라 이 사이로 울리는 '즈' 소리입니다.",
     "zero → 'jero'", "zero: /z/ 진동음"),
    ("pronunciation:added_vowel", "끝소리에 모음 추가", "Added vowel sounds",
     "자음으로 끝나는 단어 뒤에 '으' 소리를 붙이지 않습니다.",
     "desk → 'desku', check → 'checku'", "desk, check: 끝 자음에서 멈추기"),
    ("pronunciation:word_stress", "단어 강세 위치", "Word stress",
     "강세 위치가 틀리면 알아듣기 어렵습니다.",
     "development → 'DE-vel-op-ment'", "development → 'de-VEL-op-ment'"),
    ("pronunciation:final_consonant", "끝 자음 생략", "Dropped final consonants",
     "끝 자음(-t, -d, -s)을 빠뜨리지 않고 발음합니다.",
     "I need the report → 'I nee the repor'", "need, report: 끝소리 살리기"),
    # --- fluency ---
    ("fluency:short_answers", "너무 짧은 대답", "Very short answers",
     "Yes/No 뒤에 이유나 정보를 한 문장 더 붙여 보세요.",
     "Yes.", "Yes, we received it this morning and we're reviewing it now."),
    ("fluency:long_pauses_fillers", "긴 침묵·군말", "Long pauses and fillers",
     "생각할 시간이 필요하면 'Let me check that for a second.'처럼 말합니다.",
     "Uh... um... uh...", "Let me check that for a second."),
]

PATTERNS: dict[str, Pattern] = {row[0]: Pattern(*row) for row in _RAW}

CATEGORY_PRESSURE_EN: dict[str, str] = {
    "preposition": "Naturally ask about deadlines, dates, times and who the user will contact.",
    "article": "Ask the user to describe documents, issues and findings in full sentences.",
    "tense": "Ask what has already been done, what happened last week and what happens next.",
    "word_choice": "Ask the user to explain decisions, requests and reviews in their own words.",
    "konglish": "Create a context where the related Konglish word is tempting "
                "(complaints, negotiation, signatures, free extras, phones).",
    "politeness": "Make a demanding or difficult request that the user must decline "
                  "or redirect politely.",
    "collocation": "Talk about deadlines, efforts and issues so natural collocations are needed.",
    "grammar_other": "Ask open questions that require complete explanations.",
    "pronunciation": "Use the scenario's key terms and ask the user to repeat or confirm them.",
    "fluency": "Ask open follow-up questions that need longer answers (why, how, what if).",
}


def is_valid_key(key: str) -> bool:
    """Known pattern key or a well-formed 'other:<slug>'."""
    return key in PATTERNS or bool(_OTHER_RE.match(key))


def category_of(key: str) -> str:
    """Category of a key; unknown/other keys map to 'grammar_other'."""
    if key in PATTERNS:
        return PATTERNS[key].category
    return "grammar_other"


def label_ko(key: str) -> str:
    """Korean label; 'other:<slug>' keys fall back to the slug text."""
    if key in PATTERNS:
        return PATTERNS[key].label_ko
    return key.split(":", 1)[-1].replace("_", " ").replace("-", " ")


def pressure_point_for(key: str) -> str:
    """English instruction for the call persona to exercise this weakness."""
    return CATEGORY_PRESSURE_EN.get(category_of(key), CATEGORY_PRESSURE_EN["grammar_other"])


def keys_for_prompt() -> list[str]:
    """All keys, for inclusion in the mistake-extraction prompt."""
    return list(PATTERNS.keys())