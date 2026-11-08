from core.privacy import detect_sensitive, has_sensitive


def kinds(text):
    return {f.kind for f in detect_sensitive(text)}


def test_email_and_phone():
    assert "email" in kinds("Contact linh.nguyen@example.com")
    assert "phone" in kinds("Call me at +84 28 3823 0796")


def test_legal_entities():
    assert "legal_entity" in kinds("ABC Manufacturing Co., Ltd asked for a delay")
    assert "legal_entity" in kinds("주식회사 한빛과 미팅이 있어요")
    assert "legal_entity" in kinds("Công ty TNHH Sao Mai")


def test_precise_amount_flagged_rough_amount_ok():
    assert "amount" in kinds("The adjustment is VND 4,215,300,000")
    assert not has_sensitive("약 10억 원 정도의 수정사항이 있어요")


def test_possible_name():
    assert "possible_name" in kinds("We met Samsung Display yesterday")


def test_clean_text():
    assert not has_sensitive("Let's circle back on the inventory issue.")
    assert not has_sensitive("I need to call the Chief Accountant on Monday.")
    assert not has_sensitive("내일 고객사 재무팀장에게 일정 지연을 설명해야 해요.")