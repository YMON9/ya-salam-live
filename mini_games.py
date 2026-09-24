"""Content for Min Yidri's emoji and hidden-player modes."""

from __future__ import annotations


EMOJI_PUZZLES = [
    {"category": "دولة", "clue": "🌊 + ين", "answer": "البحرين"},
    {"category": "دولة", "clue": "🧊 + لندا", "answer": "آيسلندا"},
    {"category": "دولة", "clue": "🍵 + اد", "answer": "تشاد"},
    {"category": "دولة", "clue": "🐄 + يت", "answer": "الكويت"},
    {"category": "دولة", "clue": "🗼 + 🥐", "answer": "فرنسا"},
    {"category": "دولة", "clue": "🍕 + 🏛️", "answer": "إيطاليا"},
    {"category": "دولة", "clue": "🌸 + 🗾", "answer": "اليابان"},
    {"category": "دولة", "clue": "☕ + 🏃", "answer": "البرازيل"},
    {"category": "حيوان", "clue": "👑 + 🌳", "answer": "الأسد"},
    {"category": "حيوان", "clue": "⚫ + ⚪ + 🎋", "answer": "الباندا"},
    {"category": "حيوان", "clue": "🏜️ + 💧 + 🐾", "answer": "الجمل"},
    {"category": "حيوان", "clue": "🦘 + 👜", "answer": "الكنغر"},
    {"category": "حيوان", "clue": "🦓 + 🚸", "answer": "الحمار الوحشي"},
    {"category": "حيوان", "clue": "🌙 + 🪽 + 👂", "answer": "الخفاش"},
    {"category": "حيوان", "clue": "❄️ + 🐻", "answer": "الدب القطبي"},
    {"category": "حيوان", "clue": "🎨 + 🦎", "answer": "الحرباء"},
    {"category": "أكلة", "clue": "🍚 + 🍗 + 🥘", "answer": "كبسة"},
    {"category": "أكلة", "clue": "🥙 + 🍗 + 🧄", "answer": "شاورما"},
    {"category": "أكلة", "clue": "🧀 + 🥮 + 🍯", "answer": "كنافة"},
    {"category": "أكلة", "clue": "🫘 + 🍅 + 🫓", "answer": "فول"},
    {"category": "أكلة", "clue": "🍔 + 🧀 + 🍟", "answer": "برجر"},
    {"category": "أكلة", "clue": "🥔 + 🥚 + 🫓", "answer": "معصوب"},
    {"category": "أكلة", "clue": "🍝 + 🔴 + 🧀", "answer": "مكرونة"},
    {"category": "أكلة", "clue": "🐟 + 🍚", "answer": "صيادية"},
    {"category": "شيء", "clue": "🔑 + 🚗", "answer": "مفتاح السيارة"},
    {"category": "شيء", "clue": "📱 + ⚡", "answer": "شاحن"},
    {"category": "شيء", "clue": "🌧️ + ☂️", "answer": "مظلة"},
    {"category": "شيء", "clue": "📺 + 🔘", "answer": "ريموت"},
    {"category": "شيء", "clue": "⏰ + 🛏️", "answer": "منبه"},
    {"category": "شيء", "clue": "👓 + ☀️", "answer": "نظارة شمسية"},
    {"category": "شيء", "clue": "🧊 + 📦", "answer": "ثلاجة"},
    {"category": "شيء", "clue": "🪥 + 😁", "answer": "فرشاة أسنان"},
    {"category": "مهنة", "clue": "✂️ + 💇", "answer": "حلاق"},
    {"category": "مهنة", "clue": "✈️ + 👨‍✈️", "answer": "طيار"},
    {"category": "مهنة", "clue": "🩺 + 🏥", "answer": "طبيب"},
    {"category": "مهنة", "clue": "📸 + 💡", "answer": "مصور"},
    {"category": "مهنة", "clue": "🍳 + 👨‍🍳", "answer": "طباخ"},
    {"category": "مهنة", "clue": "📚 + 🧑‍🏫", "answer": "معلم"},
    {"category": "مكان", "clue": "✈️ + 🧳 + 🛂", "answer": "مطار"},
    {"category": "مكان", "clue": "🍿 + 🎬 + 🪑", "answer": "سينما"},
    {"category": "مكان", "clue": "🛒 + 🥫 + 💳", "answer": "سوبرماركت"},
    {"category": "مكان", "clue": "📚 + 🤫 + 🪑", "answer": "مكتبة"},
    {"category": "مكان", "clue": "🌊 + 🏖️ + ☀️", "answer": "شاطئ"},
    {"category": "مكان", "clue": "🏥 + 🚑 + 🩺", "answer": "مستشفى"},
]


IMPOSTER_WORDS = {
    "دولة": ["السعودية", "مصر", "اليابان", "إيطاليا", "فرنسا", "البرازيل", "الهند", "المغرب", "تركيا", "إسبانيا", "كندا", "أستراليا"],
    "حيوان": ["أسد", "فيل", "جمل", "بطريق", "دولفين", "زرافة", "قرد", "سلحفاة", "نمر", "كنغر", "باندا", "خفاش"],
    "أكلة": ["كبسة", "شاورما", "بيتزا", "سوشي", "كنافة", "برجر", "فول", "معصوب", "مكرونة", "سمبوسة", "بروست", "لقيمات"],
    "شيء": ["ريموت", "شاحن", "مظلة", "ثلاجة", "منبه", "سماعة", "كاميرا", "مرآة", "مفتاح", "مصعد", "مكنسة", "وسادة"],
    "مكان": ["مطار", "مستشفى", "مدرسة", "سينما", "شاطئ", "مكتبة", "مطعم", "ملعب", "فندق", "حديقة", "متحف", "سوبرماركت"],
}

