import typing
from typing import Optional

from bson import ObjectId
from pymongo import MongoClient


class DBConnection:

    def __init__(self, connection_str: str):
        client = MongoClient(connection_str)
        self.db = client['todo_backend']
        self.db.todo_tag.create_index([('tag_id', 1), ('todo_id', 1)])

    # TODOS
    def get_all_todos(self) -> typing.List:
        return [self.__hydrate_todo(self.__fix_id(todo)) for todo in list(self.db.todo.find())]

    def remove_all_todos(self) -> None:
        self.db.todo.remove({})
        self.db.todo_tag.remove({})

    def get_todo_by_id(self, todo_id: str) -> Optional[dict]:
        todo = self.db.todo.find({'_id': ObjectId(todo_id)})
        return self.__hydrate_todo(self.__fix_id(todo.next())) if todo.count() == 1 else None

    def create_todo(self, data: dict) -> str:
        """:returns new id"""
        new_id = self.db.todo.insert(data)
        return new_id

    def update_todo(self, todo_id: str, data: dict) -> bool:
        """:returns true if obj with id was found"""
        res = self.db.todo.update_one({'_id': ObjectId(todo_id)}, {'$set': data})
        return res.matched_count > 0

    def remove_todo(self, todo_id: str) -> bool:
        """:returns true if obj with id was found"""
        res = self.db.todo.delete_one({'_id': ObjectId(todo_id)})
        self.db.todo_tag.delete_many({'todo_id': todo_id})
        return res.deleted_count > 0

    # TAGS
    def get_all_tags(self) -> typing.List:
        return [self.__hydrate_tag(self.__fix_id(tag)) for tag in list(self.db.tag.find())]

    def remove_all_tags(self) -> None:
        self.db.tag.remove({})
        self.db.todo_tag.remove({})

    def get_tag_by_id(self, tag_id: str) -> Optional[dict]:
        tag = self.db.tag.find({'_id': ObjectId(tag_id)})
        return self.__hydrate_tag(self.__fix_id(tag.next())) if tag.count() == 1 else None

    def create_tag(self, data: dict) -> str:
        """:returns new id"""
        new_id = self.db.tag.insert(data)
        return new_id

    def update_tag(self, tag_id: str, data: dict) -> bool:
        """:returns true if obj with id was found"""
        res = self.db.tag.update_one({'_id': ObjectId(tag_id)}, {'$set': data})
        return res.matched_count > 0

    def remove_tag(self, tag_id: str) -> bool:
        """:returns true if obj with id was found"""
        res = self.db.tag.delete_one({'_id': ObjectId(tag_id)})
        self.db.todo_tag.delete_many({'tag_id': tag_id})
        return res.deleted_count > 0

    # TODOS-TAGS-RELATION

    def get_tags_of_todo(self, todo_id: str) -> typing.List:
        tag_relations = self.db.todo_tag.find({'todo_id': todo_id})
        return [self.__fix_id(tag) for tag in self.db.tag.find(
            {'_id': {'$in': [ObjectId(tag_relation['tag_id']) for tag_relation in list(tag_relations)]}}
        )]

    def get_todos_of_tag(self, tag_id: str) -> typing.List:
        todo_relations = self.db.todo_tag.find({'tag_id': tag_id})
        return [self.__fix_id(todo) for todo in self.db.todo.find(
            {'_id': {'$in': [ObjectId(todo_relation['todo_id']) for todo_relation in list(todo_relations)]}}
        )]

    def associate_tag_with_todo(self, todo_id: str, tag_id: str) -> None:
        self.db.todo_tag.insert_one({'todo_id': todo_id, 'tag_id': tag_id})

    # mongo db uses "_id", but we need "id"
    def remove_association(self, todo_id, tag_id) -> bool:
        res = self.db.todo_tag.delete_one({'todo_id': todo_id, 'tag_id': tag_id})
        return res.deleted_count > 0

    def remove_tag_associations(self, todo_id):
        self.db.todo_tag.delete_many({'todo_id': todo_id})

    @staticmethod
    def __fix_id(data: dict) -> dict:
        data['id'] = str(data['_id'])
        del data['_id']
        return data

    def __hydrate_todo(self, todo: dict) -> dict:
        tags = self.get_tags_of_todo(todo['id'])
        todo['tags'] = tags
        return todo

    def __hydrate_tag(self, tag: dict) -> dict:
        todos = self.get_todos_of_tag(tag['id'])
        tag['todos'] = todos
        return tag
