import logging

import aiohttp_cors
from aiohttp import web
from bson import ObjectId
from dbconnection import DBConnection

db = DBConnection('mongodb://root:todo@localhost:27017')


def get_all_todos(request):
    return web.json_response(db.get_all_todos())


def remove_all_todos(request):
    db.remove_all_todos()
    return web.Response(status=204)


def get_one_todo(request):
    todo_id = str(request.match_info['id'])
    todo = db.get_todo_by_id(todo_id)
    return web.json_response({'error': 'Todo not found'}, status=404) if todo is None else web.json_response(todo)


async def create_todo(request):
    data = await request.json()

    if 'title' not in data:
        return web.json_response({'error': '"title" is a required field'})
    title = data['title']
    if not isinstance(title, str) or not len(title):
        return web.json_response({'error': '"title" must be a string with at least one character'})

    data['completed'] = bool(data.get('completed', False))
    new_id = db.create_todo(data)
    url = str(request.url.join(request.app.router['one_todo'].url_for(id=str(new_id))))
    db.update_todo(
        new_id,
        {"url": url}
    )

    return web.Response(
        headers={'Location': url},
        status=303
    )


async def update_todo(request):
    todo_id = str(request.match_info['id'])

    data = await request.json()
    found = db.update_todo(todo_id, data)

    return web.json_response(db.get_todo_by_id(todo_id)) if found \
        else web.json_response({'error': 'Todo not found'}, status=404)


def remove_todo(request):
    todo_id = str(request.match_info['id'])
    found = db.remove_todo(todo_id)
    return web.Response(status=204) if found else web.json_response({'error': 'Todo not found'})


def get_all_tags(request):
    return web.json_response(db.get_all_tags())


def remove_all_tags(request):
    db.remove_all_tags()
    return web.Response(status=204)


def get_one_tag(request):
    tag_id = str(request.match_info['id'])
    tag = db.get_tag_by_id(tag_id)
    return web.json_response({'error': 'Tag not found'}, status=404) if tag is None else web.json_response(tag)


async def create_tag(request):
    data = await request.json()

    if 'title' not in data:
        return web.json_response({'error': '"title" is a required field'})
    title = data['title']
    if not isinstance(title, str) or not len(title):
        return web.json_response({'error': '"title" must be a string with at least one character'})

    tag_id = db.create_tag(data)
    url = str(request.url.join(request.app.router['one_tag'].url_for(id=str(tag_id))))
    db.update_tag(tag_id, {"url": url})

    return web.Response(
        headers={'Location': url},
        status=303
    )


async def update_tag(request):
    tag_id = str(request.match_info['id'])

    data = await request.json()
    found = db.update_tag(tag_id, data)

    return web.json_response(db.get_tag_by_id(tag_id)) if found \
        else web.json_response({'error': 'Tag not found'}, status=404)


def remove_tag(request):
    tag_id = str(request.match_info['id'])
    found = db.remove_tag(tag_id)
    return web.Response(status=204) if found else web.json_response({'error': 'Tag not found'})


def get_tags_of_todo(request):
    todo_id = str(request.match_info['id'])

    todo = db.get_todo_by_id(todo_id)
    if todo is None:
        return web.json_response({'error': 'Todo not found'})

    return web.json_response(todo['tags'] or [])


def get_todos_of_tag(request):
    tag_id = str(request.match_info['id'])

    tag = db.get_tag_by_id(tag_id)
    if tag is None:
        return web.json_response({'error': 'Tag not found'})

    return web.json_response(tag['todos'] or [])


async def associate_tag_with_todo(request):
    todo_id = str(request.match_info['id'])

    todo = db.get_todo_by_id(todo_id)
    if todo is None:
        return web.json_response({'error': 'Todo not found'})

    data = await request.json()
    tag_id = data['id']
    if not isinstance(tag_id, str) or not len(tag_id):
        return web.json_response({'error': '"id" must be a string with at least one character'})

    tag = db.get_tag_by_id(tag_id)
    if tag is None:
        return web.json_response({'error': 'Tag not found'})

    db.associate_tag_with_todo(todo_id, tag_id)
    return web.Response(status=204)


def remove_tags_from_todo(request):
    todo_id = str(request.match_info['id'])

    todo = db.get_todo_by_id(todo_id)
    if todo is None:
        return web.json_response({'error': 'Todo not found'})

    db.remove_tag_associations(todo_id)
    return web.Response(status=204)


def remove_tag_from_todo(request):
    todo_id = str(request.match_info['id'])
    tag_id = str(request.match_info['tag_id'])

    todo = db.get_todo_by_id(todo_id)
    if todo is None:
        return web.json_response({'error': 'Todo not found'})

    tag = db.get_tag_by_id(tag_id)
    if tag is None:
        return web.json_response({'error': 'Tag not found'})

    found = db.remove_association(todo_id, tag_id)
    return web.Response(status=204) if found else web.json_response({'error': 'Association not found'})


# mongo db uses "_id", but we need "id"
def fix_id(data: dict):
    data['id'] = str(data['_id'])
    del data['_id']
    return data


app = web.Application()

# Configure default CORS settings.
cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*",
        allow_methods="*",
    )
})

cors.add(app.router.add_get('/todos/', get_all_todos, name='all_todos'))
cors.add(app.router.add_delete('/todos/', remove_all_todos, name='remove_todos'))
cors.add(app.router.add_post('/todos/', create_todo, name='create_todo'))
cors.add(app.router.add_get('/todos/{id}', get_one_todo, name='one_todo'))
cors.add(app.router.add_patch('/todos/{id}', update_todo, name='update_todo'))
cors.add(app.router.add_delete('/todos/{id}', remove_todo, name='remove_todo'))
cors.add(app.router.add_post('/todos/{id}/tags/', associate_tag_with_todo, name='associate_tag_with_todo'))
cors.add(app.router.add_get('/todos/{id}/tags/', get_tags_of_todo, name='get_tags_of_todo'))
cors.add(app.router.add_delete('/todos/{id}/tags/{tag_id}', remove_tag_from_todo, name='remove_tag_from_todo'))
cors.add(app.router.add_delete('/todos/{id}/tags/', remove_tags_from_todo, name='remove_tags_from_todo'))

cors.add(app.router.add_get('/tags/', get_all_tags, name='all_tags'))
cors.add(app.router.add_delete('/tags/', remove_all_tags, name='remove_tags'))
cors.add(app.router.add_post('/tags/', create_tag, name='create_tag'))
cors.add(app.router.add_get('/tags/{id}', get_one_tag, name='one_tag'))
cors.add(app.router.add_patch('/tags/{id}', update_tag, name='update_tag'))
cors.add(app.router.add_delete('/tags/{id}', remove_tag, name='remove_tag'))
cors.add(app.router.add_get('/tags/{id}/todos/', get_todos_of_tag, name='get_todos_of_tag'))

logging.basicConfig(level=logging.DEBUG)
web.run_app(app, port=8080)
