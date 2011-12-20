import parseme

parseme.Project(
	parseme.Section('TEST',
		parseme.Round(
			a = 1
		),
	)
).parse('test.parseme.c')

print('--------------')
print(open('test.c', 'r').read())
