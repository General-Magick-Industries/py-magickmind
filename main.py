from libs.super_brain import SuperBrain

super_brain = SuperBrain(include_semetic_memory=True)
answer = super_brain.think(question="Who is Michael Jackson?", iterations=1)
print(answer)
